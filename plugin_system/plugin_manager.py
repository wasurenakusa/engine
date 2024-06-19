import contextlib
import importlib.util
import inspect
import logging
import subprocess
import sys
from abc import ABC
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

from packaging.specifiers import SpecifierSet
from packaging.version import parse as parse_version

from models.character import CharacterModel, PluginModel


class PluginManager:
    plugin_configs: list[PluginModel]

    def __init__(self, character: CharacterModel) -> None:
        self.__character = character
        self.__registered_plugin_types: list = []
        self.__plugin_type_map: dict = {}
        self.__register_plugin_type()

        # Loaded plugins are the class of the plugin only, its not initialized yet
        self.__loaded_plugins: list[type] = []
        self.__loaded_plugin_function_class_map: dict = {}

        for fn_name in self.__plugin_type_map:
            self.__loaded_plugin_function_class_map[fn_name] = []
        self.__load_all_plugins()

        # registered plugins are initialized classes, these are later used to do plugin calls.

        # for a overview of reqistered plugins
        self.__registered_plugins: list = []
        self.__registered_plugins_function_map: dict = {}

        for fn_name in self.__plugin_type_map:
            self.__registered_plugins_function_map[fn_name] = []

        # the character config plugin config name represents the class name of the plugin for now iterate over the list of plugins,
        self.__register_plugins()

        print(self.__registered_plugins_function_map)

    def __register_plugins(self):
        from plugin_system.abc.plugin import Plugin

        def add_to_registered_plugins_function_map(plugin: Plugin):
            for k, v in self.__loaded_plugin_function_class_map.items():
                if plugin in v:
                    self.__registered_plugins_function_map[k].append(plugin)

        for plugin_config in self.__character.plugins:
            plugin_class = self.__get_loaded_plugin_class_by_name(plugin_config.name)
            if not plugin_class:
                logging.warning(f"Plugin {plugin_config.name} not found. continue")
                continue

            initialized = plugin_class(self)
            self.__registered_plugins.append(initialized)
            add_to_registered_plugins_function_map(plugin_class)

    def __get_loaded_plugin_class_by_name(self, name: str):
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

    def __load_all_plugins(self) -> None:
        """
        Load plugins from the plugin path.

        """
        from plugin_system.abc.plugin import Plugin

        external_plugin_folders = [folder for folder in Path("plugins").glob("*") if folder.is_dir()]
        builtin_plungin_folders = [folder for folder in Path("plugins_builtin").glob("*") if folder.is_dir()]

        external_plugin_classes = self.__load_plugins_from_folder(external_plugin_folders, is_external=True)
        internal_plugin_classes = self.__load_plugins_from_folder(builtin_plungin_folders, is_external=False)
        # external plugins get into the list first, so external plugins can override a internal plugin completly
        # (for example to patch a behaviour etc.)
        all_plugin_classes = external_plugin_classes + internal_plugin_classes

        for plugin_class in all_plugin_classes:
            # get all the keys in self.registered_plugin_types where plugin_class is inside the list
            for base_class in inspect.getmro(plugin_class):
                if base_class in [plugin_class, Plugin, ABC, object]:
                    continue

                for k, v in self.__plugin_type_map.items():
                    if base_class in v:
                        self.__loaded_plugin_function_class_map[k].append(plugin_class)
                pass
        # self.plugin_setup()

    def __load_plugins_from_folder(self, plugin_folders: list[Path], *, is_external: bool) -> list:
        plugin_classes = []
        with PluginManager.add_to_sys_path(Path("plugins" if is_external else "plugins_builtin")):
            for plugin_path in plugin_folders:
                plugin_class = self.__load_plugin(plugin_path, is_external=is_external)
                self.__loaded_plugins.append(plugin_class)
                if plugin_class:
                    plugin_classes.append(plugin_class)
        return plugin_classes

    def __load_plugin(self, plugin_path: Path, *, is_external: bool):
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
        from plugin_system.abc.plugin import Plugin

        module_name = plugin_path.name
        try:
            plugin_module = importlib.import_module(module_name)
        except ImportError as e:
            logging.exception("Failed to import module %s", module_name)
            return False
        try:
            plugin_class: Plugin = plugin_module.PluginMainClass
        except AttributeError:
            logging.exception("Failed to find PluginMainClass in module %s, module will not be loaded!", module_name)
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
            logging.exception("Failed to install package %s, maybe you need to install the dependency by hand", package)
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
                logging.info("Installing package: %s", d)
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

    def get_plugin_config(self, name: str) -> dict:
        """
        Retrieves the configuration for a plugin with the given name.

        Args:
            name (str): The name of the plugin.

        Returns:
            dict or None: The configuration for the plugin if found, None otherwise.
        """
        for p in self.__character.plugins:
            if p.name == name:
                if p.config is None:
                    return {}
                return p.config
        return None

    def plugin_setup(self) -> None:
        """
        Every plugin inplementation should have the plugin_setup method as it could not be called by hooks (because the
        hookspecs would get into the way) we call it directly in the order the plugins where registered
        """
        for plugin in self.pm.get_plugins():
            plugin.plugin_setup()
