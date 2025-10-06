
from datetime import datetime, timezone
from typing import Dict

from models import Job

RATE_SECONDS = 30
store: Dict[str, Job] = {}
next_allowed: datetime = datetime.now(timezone.utc)

def _now() -> datetime:
    return datetime.now(timezone.utc)

def _retry_after() -> int:
    delta = (next_allowed - _now()).total_seconds()
    return max(0, int(delta))