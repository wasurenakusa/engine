from pydantic import BaseModel


class PluginModel(BaseModel):
    name: str
    config: dict | None


class CharacterModel(BaseModel):
    name: str
    author: str
    plugins: list[PluginModel]
