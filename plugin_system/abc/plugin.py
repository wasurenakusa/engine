from abc import ABC, abstractmethod

from models.character import PluginModel
from plugin_system.plugin_manager import PluginManager


class Plugin(ABC):
    pm: PluginManager

    def __init__(self, pm: PluginManager) -> None:
        self.pm = pm

    @abstractmethod
    def plugin_setup(self) -> None:
        """
        Used to setup the plugin, e.g. retriving stuff from config or similar aka stuff we would normaly
        do in a __init__ function (db initialization etc). The plugin configuration should be inside the character yaml
        under the main_class name of the plugin. This way other plugins can access the configuration too.
        """

    def get_plugin_by_name(self, name: str, plugins: list[PluginModel]) -> PluginModel:
        """
        Retrieves a plugin from the given list of plugins by its name.

        Args:
            name (str): The name of the plugin to retrieve.
            plugins (List[PluginModel]): The list of plugins to search in.

        Returns:
            PluginModel or None: The plugin with the specified name, or None if not found.
        """
        for p in plugins:
            if p.name == name:
                return p
        return None
