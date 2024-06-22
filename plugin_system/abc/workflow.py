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
    async def start_workflow(self, ctx: Context) -> None:
        """
        The workflow is called via the plugin manager, it should check it ctx.workflow if it should run or not by
        comparing the workflow_name. This function should be called by ChannelReciver Plugins
        """

    async def get_memory(self, ctx: Context) -> None:
        pass

    async def gather_system_prompts(self, ctx: Context) -> None:
        ctx.system_prompts.extend(
            item for sublist in await self.pm.call("generate_system_prompts", ctx=ctx).all() for item in sublist
        )

    async def prepare_llm_functions(self, ctx: Context) -> None:
        ctx.llm_functions.extend(
            item for sublist in await self.pm.call("generate_llm_functions", ctx=ctx).all_async() for item in sublist
        )  # while it uses the ctx it does not change it so we should be save to do it with all_async

    async def call_llm(self, ctx: Context) -> None:
        pass

    async def add_memory(self, ctx: Context) -> None:
        pass

    async def reply(self, ctx: Context) -> None:
        await self.pm.call("emit", ctx=ctx).all_async()
        # I think its okay to use async here again, the ctx should not change anymore atleast not in the reply part
