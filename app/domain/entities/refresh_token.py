from dataclasses import dataclass
from datetime import datetime


@dataclass
class RefreshToken:
    id: int | None = None
    user_id: int = 0
    jti: str = ""
    revoked: bool = False
    expires_at: datetime | None = None
    created_at: datetime | None = None
