import os

from interactions import DM, Client, Intents
from interactions.api.events import MessageCreate, Startup

from models.context import Context
from models.request import RequestModel
from plugin_system.abc.emitter import EmitterPlugin
from plugin_system.abc.reciver import ReciverPlugin


class DiscordChannel(ReciverPlugin, EmitterPlugin):
    async def plugin_setup(self) -> None:
        config = self.pm.get_plugin_config(self.__class__.__name__)
        if config:
            self.config = config
        self.client = Client(intents=Intents.MESSAGES | Intents.GUILDS)

    async def emit(self, ctx: Context) -> None:
        if ctx.emitter != self.__class__.__name__:
            return
        self.logger.info("Sending response")
        user = await self.client.fetch_user(ctx.user)
        if ctx.response and (ctx.response.message or len(ctx.response.files) > 0):
            await user.send(ctx.response.message, files=ctx.response.files)

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
            request = RequestModel(message=event.message.content)
            await self.call_workflow(request, user=str(event.message.author.id))

        await self.client.astart(os.getenv("DISCORD_API_TOKEN"))
