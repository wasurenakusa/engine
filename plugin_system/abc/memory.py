from abc import abstractmethod

from models.context import Context
from models.system_prompt import SystemPrompt
from plugin_system.abc.plugin import Plugin


class MemoryPlugin(Plugin):
    """
    This plugin allows to save and retrieve a conversation, additionally by combining this with a SystemPromptPlugin and
    or llm functions you can even provide condensed memories of older conversations
    """

    @abstractmethod
    def save_to_memory(self, ctx: Context) -> list[SystemPrompt]:
        """
        This function should save the current conversation somewhere
        """

    @abstractmethod
    def retrive_memory(self, ctx: Context) -> list[SystemPrompt]:
        """
        This function should retrive the last n amount of messages of a conversation, can additionally be used to
        retrive even older memories
        """
