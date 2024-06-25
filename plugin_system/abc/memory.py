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
    async def save_to_long_memory(self, ctx: Context) -> list[SystemPrompt]:
        """
        This function should save the current conversation somewhere
        """

    @abstractmethod
    async def save_to_short_memory(self, ctx: Context) -> list[SystemPrompt]:
        """
        This function should save the current conversation into the short memory (most likeley inmemory)
        """

    @abstractmethod
    async def retrive_memory(self, ctx: Context) -> list[SystemPrompt]:
        """
        This function should retrive the last n amount of messages of a conversation, can additionally be used to
        retrive even older memories
        """
