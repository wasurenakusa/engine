from pathlib import Path

import typer

from models.context import Context
from models.payload import RequestPayload
from plugin_system.abc.channel_sender import ChannelSenderPlugin
from plugin_system.abc.llm_function import LlmFunctionPlugin
from plugin_system.abc.memory import MemoryPlugin
from plugin_system.abc.reciver import ReciverPlugin
from plugin_system.abc.system_prompt_module import SystemPromptPlugin
from plugin_system.abc.workflow import WorkflowPlugin
from plugin_system.plugin_manager import PluginManager
from utilities.config_loader import load_character_config


def main(character_config_file: str) -> None:
    character_config = load_character_config(Path(character_config_file))
    pm = PluginManager(character_config)

    # pm.load_and_register_plugins()

    # ctx = Context(
    #     character=character_config,
    #     request_payload=RequestPayload(),
    #     workflow="test",
    #     channel="test",
    #     memory=[],
    #     llm_functions=[],
    #     system_prompts=[],
    # )
    # pm.hook.start_workflow(ctx=ctx)
    # print(pm.pm.list_name_plugin())


if __name__ == "__main__":
    typer.run(main)
