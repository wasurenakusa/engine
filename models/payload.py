from typing import Any

from pydantic import BaseModel


class RequestPayload(BaseModel):
    message: str | None = None
    file: list[bytes] | None = None
    other: Any = None
