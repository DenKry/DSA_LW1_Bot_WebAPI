
from typing import Literal
from pydantic import BaseModel
from datetime import datetime, timezone


State = Literal["NEW", "WAIT_RATE", "CALLING", "DONE", "FAILED"]

class NewJob(BaseModel):
    reqNo:          str
    message:        str

class Job(BaseModel):
    reqNo:          str
    message:        str
    state:          State = "NEW"
    reply:          str | None = None
    error:          str | None = None
    created_at:     datetime = datetime.now(timezone.utc)
    updated_at:     datetime = datetime.now(timezone.utc)