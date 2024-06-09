from pathlib import Path

import yaml

from models.character import CharacterModel


def load_character_config(path: Path) -> CharacterModel:
    with path.open(encoding="utf-8") as y:
        config = yaml.safe_load(y)
        return CharacterModel(**config)
