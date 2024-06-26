from copy import deepcopy

from pydantic_settings import BaseSettings

from models.context import Context
from plugin_system.abc.workflow import WorkflowPlugin


class DefaultWorkflowPluginConfig(BaseSettings):
    pass


class DefaultWorkflowPlugin(WorkflowPlugin):
    config: DefaultWorkflowPluginConfig

    async def plugin_setup(self) -> None:
        self.load_config(DefaultWorkflowPluginConfig)

    async def start_workflow(self, ctx: Context) -> None:
        workflow_ctx: Context = deepcopy(ctx)

        self.logger.info("Starting default workflow")

        await self.get_shortterm_memory(workflow_ctx)

        await self.gather_system_prompts(workflow_ctx)

        await self.gather_llm_functions(workflow_ctx)

        await self.update_status(workflow_ctx)

        await self.call_llm(workflow_ctx)

        await self.reply(workflow_ctx)

        await self.add_to_shortterm_memory(workflow_ctx)
