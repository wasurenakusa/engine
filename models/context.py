from typing import Any

from pydantic import BaseModel

from models.character import CharacterModel
from models.llm_function import LlmFunction
from models.message import MessageModel
from models.request import RequestMessageModel
from models.response import ResponseMessageModel
from models.system_prompt import SystemPrompt


class Context(BaseModel):
    character: CharacterModel | None = None
    request: RequestMessageModel | None = None
    response: ResponseMessageModel | None = None
    workflow: str | None = None
    system_prompts: list[SystemPrompt] | None = None
    llm_functions: list[LlmFunction] | None = None
    shortterm_memory: list[MessageModel] | None = None
    listener: str = None
    emitter: str = None
    user: Any = None
