import tomllib
from pathlib import Path


def get_version() -> str:  #
    with Path.open(Path("pyproject.toml"), "rb") as f:
        data = tomllib.load(f)
        return data["tool"]["poetry"]["version"]
