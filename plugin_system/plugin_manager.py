import contextlib
import importlib.util
import inspect
import logging
import subprocess
import sys
from abc import ABC
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import TYPE_CHECKING

from packaging.specifiers import SpecifierSet
from packaging.version import parse as parse_version

from models.character import CharacterModel, PluginModel
from plugin_system.call_builder import CallBuilder
from utilities.logging import get_logger

if TYPE_CHECKING:
    from plugin_system.abc.plugin import Plugin

logger = get_logger("engine.pm")


class PluginManager:
    plugin_configs: list[PluginModel]

    def __init__(self, character: CharacterModel) -> None:
        self.__character = character

        # registered plugins are the base abstract classes of the plugins, they are used to check if a plugin is
        # properly implemented
        self.__registered_plugin_types: list[Plugin] = []
        self.__plugin_type_map: dict = {}
        self.__register_plugin_type()
        logger.debug("%s Plugin types registered", len(self.__registered_plugin_types))

        # Loaded plugins are the class of the actual plugins only, they are not instantiated yet.
        self.__loaded_plugins: list[type] = []
        self.__loaded_plugin_function_class_map: dict = {}
        for fn_name in self.__plugin_type_map:
            self.__loaded_plugin_function_class_map[fn_name] = []
        self.__load_all_plugins()
        logger.info("%s Plugins are loaded and available to be activated", len(self.__loaded_plugins))

        # activated plugins are instantiated classes, these are later used to do plugin calls.
        self.__activated_plugins: list = []
        self.__activated_plugins_fn_map: dict = {}
        for fn_name in self.__plugin_type_map:
            self.__activated_plugins_fn_map[fn_name] = []

        # Based on the character config we activate the plugins
        self.__activate_plugins()
        logger.info("%s Plugins have been activated", len(self.__activated_plugins))

        # log the names of the activated plugins
        activated_plugin_names = []
        for plugin in self.__activated_plugins:
            activated_plugin_names.append(plugin.__class__.__name__)
        logger.info("Activated plugins: %s", activated_plugin_names)

        # All plugins are activated now, we can call the plugin_setup method of each plugin (this way if a plugin wants
        # to call a plugin method of another plugin it can do so without any problems)
        logger.info("Initializing plugins to be ready for use")
        self.__plugin_setup()
        logger.info("All plugins are ready to be used!")

    def __add_to_fn_map(self, plugin: type["Plugin"]) -> None:
        """
        Adds the given plugin to the function map.

        Args:
            plugin (type["Plugin"]): The plugin to be added.

        Raises:
            TypeError: If the plugin is a class instead of an instance.

        """
        for k, v in self.__loaded_plugin_function_class_map.items():
            if inspect.isclass(plugin):
                msg = "This is a class not a instance!! We should not be here at all!"
                raise TypeError(msg)
            if plugin.__class__ in v:
                self.__activated_plugins_fn_map[k].append(plugin)

    def __activate_plugins(self) -> None:
        """
        Activates the plugins specified in the character's plugin configuration.

        This method iterates over the plugins specified in the character's plugin configuration
        and activates each plugin by calling the __activate_plugin method.

        If a plugin is not found, a warning message is logged and the iteration continues to the next plugin.

        Returns:
            None
        """
        for plugin_config in self.__character.plugins:
            plugin_class = self.__loaded_plugin_class_by_name(plugin_config.name)
            if not plugin_class:
                logger.warning(f"Plugin {plugin_config.name} not found. continue")
                continue

            self.__activate_plugin(plugin_class)

    def __activate_plugin(self, plugin_class: type["Plugin"]) -> None:
        """
        Activates a plugin by initializing an instance of the specified plugin class,
        adding it to the list of activated plugins, and adding its functions to the function map.

        Args:
            plugin_class (type["Plugin"]): The class of the plugin to activate.

        Returns:
            None
        """
        initialized = plugin_class(self)
        self.__activated_plugins.append(initialized)
        self.__add_to_fn_map(initialized)

    def __loaded_plugin_class_by_name(self, name: str) -> type["Plugin"] | None:
        """
        Retrieves the loaded plugin class by its name.

        Args:
            name (str): The name of the plugin class.

        Returns:
            type["Plugin"] | None: The loaded plugin class if found, None otherwise.
        """
        for loaded_plugin in self.__loaded_plugins:
            if loaded_plugin.__name__ == name:
                return loaded_plugin
        return None

    def __register_plugin_type(self) -> None:
        from plugin_system.abc import base_plugin_types

        for plugin_type in base_plugin_types:
            plugin_type_call_functions = {name for name in plugin_type.__abstractmethods__}
            self.__registered_plugin_types.append(plugin_type)

            for ptfn in plugin_type_call_functions:
                if not self.__plugin_type_map.get(ptfn, None):
                    self.__plugin_type_map[ptfn] = [plugin_type]
                elif plugin_type not in self.__plugin_type_map[ptfn]:
                    self.__plugin_type_map[ptfn].append(plugin_type)

    def __load_all_plugins(self) -> None:
        """
        Load all plugins from external and internal plugin folders.

        This method searches for plugin folders in the 'plugins' and 'plugins_builtin' directories.
        It loads the plugins from these folders and adds them to the list of loaded plugin classes.
        The loaded plugin classes are then mapped to their corresponding plugin types.

        Note: External plugins have higher priority and can override internal plugins. If a plugin with the same name is
        found in both the external and internal plugin folders, the external plugin will be loaded.

        Returns:
            None
        """
        external_plugin_folders = [folder for folder in Path("plugins").glob("*") if folder.is_dir()]
        builtin_plugin_folders = [folder for folder in Path("plugins_builtin").glob("*") if folder.is_dir()]

        external_plugin_classes = self.__load_plugins_from_folder(external_plugin_folders, is_external=True)
        internal_plugin_classes = self.__load_plugins_from_folder(builtin_plugin_folders, is_external=False)
        all_plugin_classes = external_plugin_classes + internal_plugin_classes

        from plugin_system.abc.plugin import Plugin

        for plugin_class in all_plugin_classes:
            for base_class in inspect.getmro(plugin_class):
                if base_class in [plugin_class, Plugin, ABC, object]:
                    continue

                for k, v in self.__plugin_type_map.items():
                    if base_class in v:
                        self.__loaded_plugin_function_class_map[k].append(plugin_class)
                pass

    def __load_plugins_from_folder(self, plugin_folders: list[Path], *, is_external: bool) -> list:
        plugin_classes = []
        with PluginManager.add_to_sys_path(Path("plugins" if is_external else "plugins_builtin")):
            for plugin_path in plugin_folders:
                plugin_class = self.__load_plugin(plugin_path, is_external=is_external)
                self.__loaded_plugins.append(plugin_class)
                if plugin_class:
                    plugin_classes.append(plugin_class)
        return plugin_classes

    def __load_plugin(self, plugin_path: Path, *, is_external: bool) -> type["Plugin"]:
        """
        Loads a plugin from the given plugin_path. Installs the dependencies of external plugins too.
        And registers it to the plugin manager.

        Args:
            plugin_path (Path): The path to the plugin module.
            is_external (bool): Indicates whether the plugin is external or not.

        Raises:
            ImportError: If the plugin module fails to import.
            AttributeError: If the plugin module does not contain the required 'main_class'.

        Returns:
            bool: True if the plugin was loaded, False otherwise.
        """

        # Lazy load to preven circular imports
        from plugin_system.abc.plugin import Plugin

        module_name = plugin_path.name
        try:
            plugin_module = importlib.import_module(module_name)
        except ImportError as e:
            logger.exception("Failed to import module %s", module_name)
            return False
        try:
            plugin_class: Plugin = plugin_module.PluginMainClass
        except AttributeError:
            logger.exception("Failed to find PluginMainClass in module %s, module will not be loaded!", module_name)
            return False

        for bc in inspect.getmro(plugin_class):
            if bc in [plugin_class, Plugin, ABC, object]:
                continue
            # check if there are any base classes pressent we dont support if so, ignore the plugin
            if bc not in self.__registered_plugin_types:
                return False

        # internal plugin dependencies should be handled by the main requirements list, so we only handle
        # dependencies for external plugins!
        if is_external:
            self.__handle_dependencies(plugin_module)
        return plugin_class

    def __is_installed(self, package_and_version: str) -> bool:
        """
        Check if a package with a specific version is installed.

        Args:
            package_and_version (str): The package name and version in the format "package==version".
            Version can be pip compatible or poetry style versioning.

        Returns:
            bool: True if the package with the specified version is installed, False otherwise.
        """
        try:
            package, version_specifier = package_and_version.split("==")
            version_specifier = self.__convert_caret_to_pip(version_specifier)
            installed_version = parse_version(version(package))
            return installed_version in SpecifierSet(version_specifier)
        except PackageNotFoundError:
            return False

    def __install_package(self, package: str) -> bool:
        """
        Install a Python package using pip.

        Args:
            package (str): The name of the package to install.

        Raises:
            CalledProcessError: If the installation process fails.

        Returns:
            bool: True if package was installed successfully, False otherwise.
        """
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])  # noqa: S603 plugins always can run abitrary code (they can simply call exactly that so why bother?)
        except subprocess.CalledProcessError:
            logger.exception("Failed to install package %s, maybe you need to install the dependency by hand", package)
            return False
        return True

    def __handle_dependencies(self, plugin_module: any) -> None:
        """
        Handles the dependencies of a plugin module.

        Args:
            plugin_module: The plugin module to handle dependencies for.
        """
        for d in getattr(plugin_module, "dependencies", []):
            if not self.__is_installed(d):
                logger.info("Installing package: %s", d)
                self.__install_package(d)

    @contextlib.contextmanager
    @staticmethod
    def add_to_sys_path(path: str):  # noqa: ANN205
        """
        Adds a given path to the sys.path list at the beginning, allowing modules in that path to be imported.

        Args:
            path (str): The path to be added to sys.path.
        """
        sys.path.insert(0, str(path))
        try:
            yield
        finally:
            sys.path.pop(0)

    def get_plugin_config(self, plugin_name: str) -> dict:
        """
        Retrieves the configuration for a plugin with the given name.

        Args:
            name (str): The name of the plugin.

        Returns:
            dict or None: The configuration for the plugin if found, None otherwise.
        """
        for p in self.__character.plugins:
            if p.name == plugin_name:
                if p.config is None:
                    return {}
                return p.config
        return None

    def __convert_caret_to_pip(self, version_specifier: str) -> str:
        """
        Converts a caret version specifier to a pip-compatible version specifier.

        Args:
            version_specifier (str): The version specifier.

        Returns:
            str: The pip-compatible version specifier.
        """
        if version_specifier.startswith("^"):
            major_version = version_specifier[1:].split(".")[0]
            return f"~={major_version}.0"
        return version_specifier

    def __plugin_setup(self) -> None:
        """
        Every plugin inplementation should have the plugin_setup method as it could not be called by hooks (because the
        hookspecs would get into the way) we call it directly in the order the plugins where registered
        """
        self.call("plugin_setup").all()

    def call(self, function_name: str, **kwargs: dict[str, any]) -> CallBuilder:
        """
        Calls a function in the activated plugins.

        Args:
            function_name (str): The name of the function to call.
            **kwargs (dict[str, any]): Keyword arguments to pass to the function.

        Returns:
            CallBuilder: An instance of the CallBuilder class.
        """
        return CallBuilder(self.__activated_plugins_fn_map, function_name, **kwargs)
