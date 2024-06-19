from abc import abstractmethod

from models.context import Context
from plugin_system.abc.plugin import Plugin


class ChannelSenderPlugin(Plugin):
    """
    This plugin allows to implement sending in a Channel. Your reciving function should call the recive_message hook via
    the self.pm functionality to get a message inside the engine.
    """

    channel: str

    @abstractmethod
    def send_message(self, ctx: Context, message: str) -> None:
        """
        Send a message to the Channel. Check ctx.channel with self.channel if it is acctually the intendet channel.
        """
