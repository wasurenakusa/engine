from typing import Literal

from pydantic import BaseModel


class FileModel(BaseModel):
    mimetype: str
    data: bytes


class MessageModel(BaseModel):
    role: Literal["user", "llm"]
    content: list[str | FileModel]
