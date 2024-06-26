from pydantic_settings import BaseSettings

from models.context import Context
from models.message import MessageModel
from models.system_prompt import SystemPrompt
from plugin_system.abc.memory import MemoryPlugin


class InmemoryPluginConfig(BaseSettings):
    pass


class InmemoryPlugin(MemoryPlugin):
    shortterm_memory: dict[str, list[MessageModel]]

    async def plugin_setup(self) -> None:
        self.load_config(InmemoryPluginConfig)
        self.shortterm_memory = {}

    async def save_to_longterm_memory(self, ctx: Context) -> list[SystemPrompt]:
        """
        This function should save the current conversation somewhere
        """

    async def add_to_shortterm_memory(self, ctx: Context) -> None:
        self.logger.info(
            "Adding request and response to shortterm memory for user %s",
            ctx.user_id,
        )
        if ctx.user_id not in self.shortterm_memory:
            self.shortterm_memory[ctx.user_id] = []
        self.shortterm_memory[ctx.user_id].append(ctx.request)
        self.shortterm_memory[ctx.user_id].append(ctx.response)
        ctx.shortterm_memory = self.shortterm_memory[ctx.user_id]

    async def retrive_shortterm_memory(self, ctx: Context) -> list[MessageModel]:
        if ctx.user_id not in self.shortterm_memory:
            self.shortterm_memory[ctx.user_id] = []

        self.logger.info(
            "Retrive %s memory entries from shortterm memory for user %s",
            len(self.shortterm_memory),
            ctx.user_id,
        )
        return self.shortterm_memory[ctx.user_id]
