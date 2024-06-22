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
