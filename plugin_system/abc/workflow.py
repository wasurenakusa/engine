from abc import abstractmethod

from models.context import Context
from plugin_system.abc.plugin import Plugin
from plugin_system.hook import plugin_hookspec


class WorkflowPlugin(Plugin):
    """
    A workflow plugin determins which plugins should be called at which moment in the livetime of an request. In theory,
    this allows to have multiple workflows at the same time.
    """

    name = "default"

    @plugin_hookspec
    @abstractmethod
    def start_workflow(self, ctx: Context) -> None:
        """
        The workflow is called via the plugin manager hock, it should check it ctx.workflow if it should run or not by
        comparing the workflow_name. This function should be called by ChannelReciver Plugins
        """

    def get_memory(self, ctx: Context) -> None:
        ctx.memory = ["A"]

    def gather_system_prompts(self, ctx: Context) -> None:
        print("gsp")
        ctx.system_prompts.extend(item for sublist in self.pm.hook.generate_system_prompts(ctx=ctx) for item in sublist)

    def prepare_llm_functions(self, ctx: Context) -> None:
        print("plf")
        ctx.llm_functions.extend(item for sublist in self.pm.hook.generate_llm_functions(ctx=ctx) for item in sublist)

    def call_llm(self, ctx: Context) -> None:
        pass

    def add_memory(self, ctx: Context) -> None:
        print(ctx.memory)

    def reply(self, ctx: Context) -> None:
        print(ctx.system_prompts)
