from abc import ABC, abstractmethod

from pydantic_settings import BaseSettings

from models.character import PluginModel
from plugin_system.plugin_manager import PluginManager
from utilities.logging import get_logger


class Plugin(ABC):
    pm: PluginManager

    def __init__(self, pm: PluginManager) -> None:
        self.pm = pm
        self.logger = get_logger(self.__class__.__name__)

    @abstractmethod
    async def plugin_setup(self) -> None:
        """
        Used to setup the plugin, e.g. retriving stuff from config or similar aka stuff we would normaly
        do in a __init__ function (db initialization etc). The plugin configuration should be inside the character yaml
        under the main_class name of the plugin. This way other plugins can access the configuration too.
        """

    def load_config(self, config_model: BaseSettings) -> None:
        """
        Loads the configuration from the characters plugin configuration and sets the self.config instance variable.

        Args:
            config_model (BaseSettings): The configuration model to use for loading the configuration.

        Returns:
            None
        """
        cfg = self.pm.get_plugin_config(self.__class__.__name__)
        self.config = config_model(**cfg)

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
