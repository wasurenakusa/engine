from collections.abc import Callable
from typing import Any

from pydantic import BaseModel


class LlmFnParameter(BaseModel):
    name: str
    parameter_type: str
    description: str
    required: bool


class LlmFunction(BaseModel):
    description: str
    parameters: list[LlmFnParameter]
    fn: Callable[[Any], str]
