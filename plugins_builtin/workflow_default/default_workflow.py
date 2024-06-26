from copy import deepcopy

from models.context import Context
from plugin_system.abc.workflow import WorkflowPlugin


class DefaultWorkflow(WorkflowPlugin):
    config: dict

    async def plugin_setup(self) -> None:
        config = self.pm.get_plugin_config(self.__class__.__name__)
        if config:
            self.config = config

    async def start_workflow(self, ctx: Context) -> None:
        workflow_ctx = deepcopy(ctx)
        await self.get_memory(workflow_ctx)
        await self.gather_system_prompts(workflow_ctx)
        await self.prepare_llm_functions(workflow_ctx)
        await self.call_llm(workflow_ctx)
        await self.reply(workflow_ctx)
        await self.add_memory(workflow_ctx)
