# ruff: noqa: ANN201,S101
import sys
from unittest.mock import MagicMock

from models.character import CharacterModel
from plugin_system.plugin_manager import PluginManager


def test_add_to_sys_path():
    path = "/path/to/module"
    sys_path_before = sys.path.copy()

    with PluginManager.add_to_sys_path(path):
        assert sys.path[0] == path

    assert sys.path == sys_path_before
