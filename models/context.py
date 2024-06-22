from typing import Any

from pydantic import BaseModel

from models.character import CharacterModel
from models.llm_function import LlmFunction
from models.request import RequestModel
from models.response import ResponseModel
from models.system_prompt import SystemPrompt


class Context(BaseModel):
    character: CharacterModel | None = None
    request: RequestModel | None = None
    response: ResponseModel | None = None
    workflow: str | None = None
    system_prompts: list[SystemPrompt] | None = None
    llm_functions: list[LlmFunction] | None = None
    memory: list | None = None
    listener: str = None
    emitter: str = None
    user: Any = None
