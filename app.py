
import asyncio, uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional, Literal
from fastapi import FastAPI, HTTPException, Response, status, Request
from pydantic import BaseModel
from contextlib import asynccontextmanager
import uvicorn
from dotenv import load_dotenv
import os

from botbuilder.core import BotFrameworkAdapterSettings, BotFrameworkAdapter, TurnContext, ActivityHandler
from botbuilder.schema import Activity

load_dotenv()

from models import Job, NewJob, State
from store_rate_limit import store, RATE_SECONDS, _now, _retry_after, next_allowed
from service import call_azure_bot


APP_ID = os.getenv("MicrosoftAppId")
APP_PASSWORD = os.getenv("MicrosoftAppPassword")

# BOT ADAPTER and SETUP
adapter = BotFrameworkAdapter(BotFrameworkAdapterSettings(APP_ID, APP_PASSWORD))

async def on_error(context: TurnContext, error: Exception):
    await context.send_activity("The bot encountered an error")
    raise error
adapter.on_turn_error = on_error

class EchoBot(ActivityHandler):
    async def on_message_activity(self, turn_context: TurnContext):
        await turn_context.send_activity(f"Echo: {turn_context.activity.text}")

bot = EchoBot()



async def worker_loop():
    global next_allowed
    while True:
        try:
            pending = next((j for j in store.values() if j.state in ("NEW", "WAIT_RATE")), None)
            if not pending:
                await asyncio.sleep(0.2)
                continue

            if pending.state == "NEW":
                pending.state = "WAIT_RATE"
                pending.updated_at = _now()

            if _now() < next_allowed:
                await asyncio.sleep(0.2)
                continue


            pending.state = "CALLING"
            pending.updated_at = _now()
            try:
                reply = await call_azure_bot(pending.message)
                pending.reply = reply
                pending.state = "DONE"
                pending.updated_at = _now()
            except Exception as e:
                print("Worker error:", e)
                pending.error = str(e)
                pending.state = "FAILED"
                pending.updated_at = _now()
            finally:
                next_allowed = _now() + timedelta(seconds=RATE_SECONDS)

        except Exception:
            await asyncio.sleep(0.5)



@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(worker_loop())
    yield

app = FastAPI(title="Lab1_Bot_WebAPI", version="1.0.0", lifespan=lifespan)

@app.post("/api/messages")
async def messages(request: Request):
    body = await request.json()
    activity = Activity().deserialize(body)
    auth_header = request.headers.get("Authorization", "")

    await adapter.process_activity(activity, auth_header, bot.on_turn)
    return Response(status_code=200)

@app.post("/jobs", status_code=status.HTTP_201_CREATED)
def create_job(payload: NewJob):
    if payload.reqNo in store:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="reqNo already exists")
    job = Job(reqNo=payload.reqNo, message=payload.message)
    store[payload.reqNo] = job
    return {"reqNo": job.reqNo, "state": "WAIT_RATE"}

@app.get("/jobs/{reqNo}/status")
def get_status(reqNo: str):
    job = store.get(reqNo)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    return {"reqNo": job.reqNo, "state": job.state, "updated_at": job.updated_at.isoformat()}

@app.get("/jobs/{reqNo}/result")
def get_result(reqNo: str, response: Response):
    job = store.get(reqNo)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")

    if job.state != "DONE":
        response.status_code = status.HTTP_429_TOO_MANY_REQUESTS
        response.headers["Retry after"] = str(max(1, _retry_after()))
        return {"reqNo": reqNo, "state": job.state, "error": "RATE_LIMIT"}

    return {"reqNo": job.reqNo, "state": "DONE", "reply": job.reply}


if __name__ == "__main__":
    uvicorn.run("app:app", host="127.0.0.1", port=8081, reload=True)