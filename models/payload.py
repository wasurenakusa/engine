from typing import Any

from pydantic import BaseModel


class Payload(BaseModel):
    message: str | None = None
    files: list[bytes] = []
    other: Any = None
