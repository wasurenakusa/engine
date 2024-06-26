import httpx
from interactions import DM, Client, Intents
from interactions.api.events import MessageCreate, Startup
from pydantic import Field
from pydantic_settings import BaseSettings

from models.context import Context
from models.message import FileModel
from models.request import RequestMessageModel
from plugin_system.abc.emitter import EmitterPlugin
from plugin_system.abc.reciver import ReciverPlugin


class DiscordPluginConfig(BaseSettings):
    api_token: str = Field(None, alias="DISCORD_API_TOKEN")  # Set
    allowed_mimetypes: list[str] = [
        "image/jpeg",
        "image/png",
        "image/gif",
        "image/webp",
    ]  # Good default as anthropic and openai support them out of the box
    allowed_size: int = 3  # in MB


class DiscordPlugin(ReciverPlugin, EmitterPlugin):
    config: DiscordPluginConfig

    async def plugin_setup(self) -> None:
        self.load_config(DiscordPluginConfig)
        self.client = Client(intents=Intents.MESSAGES | Intents.GUILDS)

    async def emit(self, ctx: Context) -> None:
        if ctx.emitter != self.__class__.__name__:
            return
        self.logger.info("Sending response")
        user = await self.client.fetch_user(ctx.user_id)
        if ctx.response and (len(ctx.response.content) > 0):
            message, files = await self.form_response_from_content(ctx.response.content)
            await user.send(message, files=files)

    async def form_response_from_content(self, content: list[str | FileModel]) -> None:
        message = ""
        files = []
        for c in content:
            if isinstance(c, str):
                message += c
            elif isinstance(c, FileModel):
                files.append(c)
        return message, files

    async def listen(self) -> None:
        @self.client.listen(Startup)
        async def start() -> None:
            self.logger.info("Listening for Discord events as %s", self.client.user.display_name)

        @self.client.listen(MessageCreate)
        async def on_message_create(event: MessageCreate) -> None:
            if event.message.author.id == self.client.user.id:
                return
            if not isinstance(event.message.channel, DM):
                return
            self.logger.info(
                "Reviced a new request from %s",
                event.message.author.username,
            )

            self.logger.info("Create Context")

            content = []
            async with httpx.AsyncClient() as client:
                for a in event.message.attachments:
                    if a.content_type not in self.config.allowed_mimetypes:
                        continue
                    if a.size > self.config.allowed_size * 2**20:
                        continue
                        # we should download the file now
                    try:
                        r = await client.get(a.url)
                        r.raise_for_status()

                        content.append(
                            FileModel(
                                mimetype=a.content_type,
                                data=r.content,
                            ),
                        )
                    except httpx.HTTPStatusError as exc:
                        self.logger.error(  # noqa: TRY400 We don't care why it failed, the status code is enough
                            f"Recived a {exc.response.status_code} error when trying to download the url: {a.url}. \
                            Ignoring this now.",
                        )
                        continue
            if event.message.content:
                content.append(event.message.content)
            message = RequestMessageModel(role="user", content=content)
            await self.call_workflow(message, user_id=str(event.message.author.id))

        await self.client.astart(self.config.api_token)

    async def update_status(self, ctx: Context) -> None:
        user = await self.client.fetch_user(ctx.user_id)
        dm_channel: DM = await user.fetch_dm()
        if dm_channel:
            await dm_channel.trigger_typing()
