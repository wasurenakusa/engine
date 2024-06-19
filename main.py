from pathlib import Path

import typer

from models.context import Context
from models.payload import RequestPayload
from plugin_system.plugin_manager import PluginManager
from utilities.config_loader import load_character_config


def main(character_config_file: str) -> None:
    character_config = load_character_config(Path(character_config_file))
    pm = PluginManager(character_config)

    # pm.load_and_register_plugins()

    ctx = Context(
        character=character_config,
        request_payload=RequestPayload(),
        workflow="test",
        channel="test",
        memory=[],
        llm_functions=[],
        system_prompts=[],
    )
    print(pm.call("generate_system_prompts", ctx=ctx).all())


if __name__ == "__main__":
    typer.run(main)
