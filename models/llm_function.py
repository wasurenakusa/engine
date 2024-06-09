from collections.abc import Callable

from pydantic import BaseModel


class LlmFnParameter(BaseModel):
    name: str
    parameter_type: str
    description: str
    required: bool


class LlmFunction(BaseModel):
    name: str  # The function name will be overriden by the llm plugin consuming it!
    description: str
    parameters: list[LlmFnParameter]
    fn: Callable
