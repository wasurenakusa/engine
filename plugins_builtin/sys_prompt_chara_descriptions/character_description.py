from pydantic_settings import BaseSettings

from models.context import Context
from models.system_prompt import SystemPrompt
from plugin_system.abc.sys_prompt import SystemPromptPlugin


class CharacterDescriptionsPluginConfig(BaseSettings):
    class Config:
        extra = "allow"


class CharacterDescriptionsPlugin(SystemPromptPlugin):
    config: CharacterDescriptionsPluginConfig

    async def plugin_setup(self) -> None:
        self.load_config(CharacterDescriptionsPluginConfig)

    async def generate_system_prompts(self, ctx: Context) -> list[SystemPrompt]:  # noqa: ARG002
        prompts = []
        for key, content in self.config.model_dump().items():
            prompts.append(self.generate_prompt(key, content))
        return prompts

    def generate_prompt(self, key: str, content: str | dict) -> SystemPrompt:
        if isinstance(content, dict):
            content = [self.generate_prompt(k, c) for k, c in content.items()]
            return SystemPrompt(name=key, content=content)
        return SystemPrompt(name=key, content=content)
