import atexit
from pathlib import Path

import anyio
import typer
from dotenv import load_dotenv

from plugin_system.plugin_manager import PluginManager
from utilities.config_loader import load_character_config
from utilities.logging import get_logger
from utilities.version import get_version

logger = get_logger("engine.main")
load_dotenv()

version = get_version()


def exit_cleanup() -> None:
    logger.warning("Engine is closing")


async def engine(character_config_file: str) -> None:
    logger.info("Loading character from file '%s'", character_config_file)
    character_config = load_character_config(Path(character_config_file))
    logger.info("Character '%s' successfully loaded", character_config.name)
    logger.info("Initialize plugin manager")
    pm = await PluginManager(character_config).init()
    logger.info("Start listening to channels")
    await pm.call("listen").all()


def main(character_config_file: str) -> None:
    atexit.register(exit_cleanup)
    logger.info("Wasurenakusa Engine version %s", version)
    anyio.run(engine, character_config_file)


if __name__ == "__main__":
    typer.run(main)
