from abc import abstractmethod

from models.context import Context
from models.message import MessageModel
from models.system_prompt import SystemPrompt
from plugin_system.abc.plugin import Plugin


class MemoryPlugin(Plugin):
    """
    This plugin allows to save and retrieve a conversation, additionally by combining this with a SystemPromptPlugin and
    or llm functions you can even provide condensed memories of older conversations
    """

    @abstractmethod
    async def save_to_longterm_memory(self, ctx: Context) -> list[SystemPrompt]:
        """
        This function should save the current conversation somewhere
        """

    @abstractmethod
    async def add_to_shortterm_memory(self, ctx: Context) -> None:
        """
        This function should save the current conversation into the short memory (most likeley inmemory)
        """

    @abstractmethod
    async def retrive_shortterm_memory(self, ctx: Context) -> list[MessageModel]:
        """
        This function should retrive the last n amount of messages of a conversation
        """
