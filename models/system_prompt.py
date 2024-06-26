from pydantic import BaseModel


class SystemPrompt(BaseModel):
    """
    A system prompt module represents a part of the system prompt. Do not use LLM specific formating etc.

    Attributes:
        name (str): The name of the module, some LLMs will omit this.
        content (str): The content of the module.
    """

    name: str
    content: str | "SystemPrompt"
