import json

import anyio
from pydantic import BaseModel
from pydantic_settings import BaseSettings

from models.context import Context
from models.message import MessageModel
from models.system_prompt import SystemPrompt
from plugin_system.abc.memory import MemoryPlugin
from plugin_system.abc.sys_prompt import SystemPromptPlugin


class SimpleMemoryModel(BaseModel):
    longterm_memory: dict[str, list[SystemPrompt]] = {}
    shortterm_memory: dict[str, list[MessageModel]] = {}


class SimpleMemoryPluginConfig(BaseSettings):
    memory_file: str = "tmp/memory.json"


class SimpleMemoryPlugin(MemoryPlugin, SystemPromptPlugin):
    config: SimpleMemoryPluginConfig
    longterm_memory: dict[str, list[SystemPrompt]]
    shortterm_memory: dict[str, list[MessageModel]]

    async def plugin_setup(self) -> None:
        self.load_config(SimpleMemoryPluginConfig)
        self.memory = await self.load_from_file()

    async def load_from_file(self) -> SimpleMemoryModel:
        # First check if the file exists and if not create it use anyio.open_file
        # Then load the file and return the data

        await self.ensure_memory_file_exists()

        async with await anyio.open_file(self.config.memory_file, "r") as f:
            content = await f.read()
            return SimpleMemoryModel.model_validate_json(content)

    async def ensure_memory_file_exists(self) -> None:
        config_memory_file = anyio.Path(self.config.memory_file)
        if not await config_memory_file.exists():
            await config_memory_file.parent.mkdir(parents=True, exist_ok=True)
            await config_memory_file.touch(exist_ok=True)
            # Write an empty json object to the file otherwise the json parser will fail on empty files ._.'
            await config_memory_file.write_text("{}")

    async def save_to_file(self) -> None:
        async with await anyio.open_file(self.config.memory_file, "w") as f:
            await f.write(self.memory.model_dump_json())

    async def save_to_longterm_memory(self, ctx: Context) -> list[SystemPrompt]:
        # We dont touch the longterm memory for now. TODO: Touch it!
        pass

    async def add_to_shortterm_memory(self, ctx: Context) -> None:
        self.logger.info(
            "Adding request and response to shortterm memory for user %s",
            ctx.user_id,
        )
        if ctx.user_id not in self.memory.shortterm_memory:
            self.memory.shortterm_memory[ctx.user_id] = []
        self.memory.shortterm_memory[ctx.user_id].append(ctx.request)
        self.memory.shortterm_memory[ctx.user_id].append(ctx.response)
        ctx.shortterm_memory = self.memory.shortterm_memory[ctx.user_id]

        # For now out of simplicity we save the whole memory to the file after each change
        await self.save_to_file()

    async def retrive_shortterm_memory(self, ctx: Context) -> list[MessageModel]:
        if ctx.user_id not in self.memory.shortterm_memory:
            self.memory.shortterm_memory[ctx.user_id] = []

        self.logger.info(
            "Retrive %s memory entries from shortterm memory for user %s",
            len(self.memory.shortterm_memory),
            ctx.user_id,
        )
        return self.memory.shortterm_memory[ctx.user_id]

    async def generate_system_prompts(self, ctx: Context) -> list[SystemPrompt]:
        return self.memory.longterm_memory.get(ctx.user_id, [])
