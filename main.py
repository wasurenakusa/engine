from pathlib import Path

import typer
from dotenv import load_dotenv

from plugin_system.plugin_manager import PluginManager
from utilities.config_loader import load_character_config

load_dotenv()


def main(character_config_file: str) -> None:
    character_config = load_character_config(Path(character_config_file))
    pm = PluginManager(character_config)

    pm.call("listen_to_channel").all()


if __name__ == "__main__":
    typer.run(main)
