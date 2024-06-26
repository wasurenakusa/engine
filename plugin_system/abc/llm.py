from abc import abstractmethod

from models.context import Context
from plugin_system.abc.plugin import Plugin


class LlmPlugin(Plugin):
    """
    This plugin allows to implement a LLM.
    """

    @abstractmethod
    async def get_llm_response(self, ctx: Context) -> None:
        """
        Here the llm we request the llm response. Its recommended to handle the ctx.llm_functions. The added
        informations from the llm functions should not endup in the memory!
        """

    class ServerNotReachableError(Exception):
        pass
