
import httpx
import asyncio
from src.config import DIRECTLINE_SECRET, DIRECTLINE_BASE

SECRET_TOKEN = DIRECTLINE_SECRET

HEADERS = {"Authorization": f"Bearer {DIRECTLINE_SECRET}"}


async def call_azure_bot(user_message: str) -> str:
    async with httpx.AsyncClient(timeout=15) as client:
        start = await client.post(f"{DIRECTLINE_BASE}/conversations", headers=HEADERS)
        if start.status_code not in (200, 201):
            raise RuntimeError(f"start failed {start.status_code}: {start.text}")
        start_data = start.json()
        conv_id = start_data.get("conversationId")
        if not conv_id:
            raise RuntimeError(f"no conversationId in start payload: {start_data}")

        send = await client.post(
            f"{DIRECTLINE_BASE}/conversations/{conv_id}/activities",
            headers=HEADERS,
            json={"type": "message", "from": {"id": "user1"}, "text": user_message},
        )
        if send.status_code not in (200, 201):
            raise RuntimeError(f"send failed {send.status_code}: {send.text}")

        watermark = None
        for _ in range(70):
            params = {"watermark": watermark} if watermark else None
            response = await client.get(
                            f"{DIRECTLINE_BASE}/conversations/{conv_id}/activities",
                            headers=HEADERS, params=params)
            if response.status_code != 200:
                raise RuntimeError(f"response failed {response.status_code}: {response.text}")
            pdata = response.json()
            watermark = pdata.get("watermark", watermark)
            acts = pdata.get("activities", [])

            for a in acts:
                if a.get("from", {}).get("id") != "user1" and a.get("type") == "message":
                    return a.get("text") or ""
            await asyncio.sleep(0.5)

        raise TimeoutError("no bot reply within timeout")