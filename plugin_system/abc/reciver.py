from abc import abstractmethod

from models.context import Context
from models.request import RequestMessageModel
from plugin_system.abc.plugin import Plugin


class ReciverPlugin(Plugin):
    """
    This plugin allows to implement reciving stuff... it is the only plugin type directly called by the engine directly!
    Every other plugins are called by other plugins (most likeley workflow plugins) normaly this will be implemented
    together with a ChannelSenderPlugin if it is a abitrary trigger, make sure to provide a default channel.
    """

    channel_name: str

    @abstractmethod
    async def listen(self) -> None:
        """
        Starts listening to a source that could trigger an workflow. If a new message or other Trigger implemented by
        this should trigger a workflow use the self.call_workflow function which creates a context and so on.
        """

    async def call_workflow(self, request: RequestMessageModel, user: str | None = None) -> None:
        """
        Calls the first workflow (aka default workflow) with the given request and user. Builds a context that is
        exists for the lifetime of the request.

        Args:
            request (RequestModel): The request object.
            user (Optional): The user object/id/whatever. Defaults to None.

        Returns:
            None
        """
        ctx = Context(
            request=request,
            listener=self.__class__.__name__,
            emitter=self.__class__.__name__,  # By default we should set the emitter to the same as listener
        )
        ctx.user = user

        await self.pm.call("start_workflow", ctx=ctx).first()
