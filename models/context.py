from typing import Optional

from pydantic import BaseModel

from models.character import CharacterModel
from models.llm_function import LlmFunction
from models.payload import RequestPayload
from models.system_prompt import SystemPrompt


class Context(BaseModel):
    character: CharacterModel | None
    request_payload: RequestPayload | None
    workflow: str | None
    channel: str | None
    system_prompts: list[SystemPrompt] | None
    llm_functions: list[LlmFunction] | None
    memory: list | None
