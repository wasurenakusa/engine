from abc import abstractmethod

from models.context import Context
from models.llm_function import LlmFunction
from plugin_system.abc.plugin import Plugin


class LlmFunctionPlugin(Plugin):
    """
    This plugin allows to implement Llm Functions.
    """

    channel: str

    @abstractmethod
    def generate_llm_functions(self, ctx: Context) -> list[LlmFunction]:
        """
        Here the llm functions of the plugin are generated.
        """
