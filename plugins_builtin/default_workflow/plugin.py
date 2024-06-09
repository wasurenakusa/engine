from models.context import Context
from plugin_system.abc.workflow import WorkflowPlugin
from plugin_system.hook import plugin_hook


class DefaultWorkflow(WorkflowPlugin):
    config: dict

    def plugin_setup(self) -> None:
        config = self.pm.get_plugin_config(self.__class__.__name__)
        if config:
            self.config = config

    @plugin_hook
    def start_workflow(self, ctx: Context) -> None:
        self.get_memory(ctx)
        self.gather_system_prompts(ctx)
        self.prepare_llm_functions(ctx)
        self.call_llm(ctx)
        self.reply(ctx)
        self.add_memory(ctx)
