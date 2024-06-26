from abc import abstractmethod

from models.context import Context
from plugin_system.abc.plugin import Plugin


class EmitterPlugin(Plugin):
    """
    This plugin allows to implement emitting a payload somewhere.
    """

    @abstractmethod
    async def emit(self, ctx: Context) -> None:
        """
        Emitt a payload to a target.
        """

    @abstractmethod
    async def update_status(self, ctx: Context) -> None:
        """
        Update the status of the conversation. This function should be called by the workflow plugin. In most cases its
        used to provide a writing status to the user.
        """
        pass
