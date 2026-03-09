from dataclasses import dataclass
from datetime import datetime


@dataclass
class EmailToken:
    id: int | None = None
    user_id: int = 0
    token: str = ""
    purpose: str = ""
    used: bool = False
    expires_at: datetime | None = None
    created_at: datetime | None = None
