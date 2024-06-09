from abc import abstractmethod

from models.context import Context
from models.payload import RequestPayload
from plugin_system.abc.plugin import Plugin
from plugin_system.hook import plugin_hookspec


class ReciverPlugin(Plugin):
    """
    This plugin allows to implement reciving stuff... it is the only plugin type directly called by the engine directly!
    Every other plugins are called by other plugins (most likeley workflow plugins) normaly this will be implemented
    together with a ChannelSenderPlugin if it is a abitrary trigger, make sure to provide a default channel.
    """

    channel_name: str

    @plugin_hookspec
    @abstractmethod
    def listen_to_channel(self) -> None:
        """
        Starts listening to a channel. If a new message or other Trigger implemented by this should trigger a workflow
        use the self.call_workflow function which creates a context and so on.
        """

    def call_workflow(self, payload: RequestPayload) -> None:
        ctx = Context(channel=self.channel_name, request_payload=payload)
        self.pm.hook.start_workflow(ctx=ctx)
