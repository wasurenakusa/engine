from pathlib import Path

import yaml

from models.character import CharacterModel


def load_character_config(path: Path) -> CharacterModel:
    with path.open("r") as f:
        config = yaml.safe_load(f)
        return CharacterModel(**config)
