from abc import abstractmethod

from models.context import Context
from models.system_prompt import SystemPrompt
from plugin_system.abc.plugin import Plugin
from plugin_system.hook import plugin_hookspec


class SystemPromptPlugin(Plugin):
    """
    This plugin allows to implement system prompt stuff the system prompt is build right at the beginning.
    """

    @plugin_hookspec
    @abstractmethod
    def generate_system_prompts(self, ctx: Context) -> list[SystemPrompt]:
        """
        This function should generate a list of SystemPromptModules that then gets merged into the system prompt by the
        LLM in the best way to handle it. SO dont do any LLM specific formating etc.
        """
