from abc import abstractmethod

from models.context import Context
from plugin_system.abc.plugin import Plugin


class WorkflowPlugin(Plugin):
    """
    A workflow plugin determins which plugins should be called at which moment in the livetime of an request. In theory,
    this allows to have multiple workflows at the same time.
    """

    name = "default"

    @abstractmethod
    def start_workflow(self, ctx: Context) -> None:
        """
        The workflow is called via the plugin manager hock, it should check it ctx.workflow if it should run or not by
        comparing the workflow_name. This function should be called by ChannelReciver Plugins
        """

    def get_memory(self, ctx: Context) -> None:
        pass

    def gather_system_prompts(self, ctx: Context) -> None:
        ctx.system_prompts.extend(
            item
            for sublist in self.pm.call("generate_system_prompts", ctx=ctx).all()
            for item in sublist
        )

    def prepare_llm_functions(self, ctx: Context) -> None:
        ctx.llm_functions.extend(
            item
            for sublist in self.pm.call("generate_llm_functions", ctx=ctx).all()
            for item in sublist
        )

    def call_llm(self, ctx: Context) -> None:
        pass

    def add_memory(self, ctx: Context) -> None:
        pass

    def reply(self, ctx: Context) -> None:
        pass
