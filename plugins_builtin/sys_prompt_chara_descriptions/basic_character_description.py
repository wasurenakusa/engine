from models.context import Context
from models.system_prompt import SystemPrompt
from plugin_system.abc.sys_prompt import SystemPromptPlugin


class BasicCharacterDescriptions(SystemPromptPlugin):
    config: dict

    async def plugin_setup(self) -> None:
        config = self.pm.get_plugin_config(self.__class__.__name__)
        if config:
            self.config = config

    async def generate_system_prompts(self, ctx: Context) -> list[SystemPrompt]:  # noqa: ARG002
        prompts = []
        # config should be a simply kv dict, this plugin simply parses this to a SystemPrompt part
        for name, description in self.config.items():
            prompts.append(SystemPrompt(name=name, text=description))
        return prompts
