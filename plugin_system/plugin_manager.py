import contextlib
import importlib.util
import logging
import subprocess
import sys
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

import pluggy
from packaging.specifiers import SpecifierSet
from packaging.version import parse as parse_version

from models.character import CharacterModel, PluginModel


class PluginManager:
    pm: pluggy.PluginManager
    plugin_configs: list[PluginModel]
    hook = pluggy.HookRelay

    def __init__(self, character: CharacterModel) -> None:
        self.pm = pluggy.PluginManager("wasurenakusa")
        self.character = character
        self.plugin_order = self.get_all_configured_plugin_names()
        self.hook = self.pm.hook
        self.register_plugin_type = self.pm.add_hookspecs

    def convert_caret_to_pip(self, version_specifier: str) -> str:
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

    def load_and_register_plugins(self) -> None:
        """
        Load plugins from the plugin path.

        """
        external_plugin_folders = [folder for folder in Path("plugins").glob("*") if folder.is_dir()]
        builtin_plungin_folders = [folder for folder in Path("plugins_builtin").glob("*") if folder.is_dir()]

        external_plugin_classes = self.load_plugins(external_plugin_folders, is_external=True)
        internal_plugin_classes = self.load_plugins(builtin_plungin_folders, is_external=False)

        # external plugins get into the list first, so external plugins can override a internal plugin completly
        # (for example to patch a behaviour etc.)
        all_plugin_classes = external_plugin_classes + internal_plugin_classes
        for plugin_name in reversed(self.plugin_order):  # reverse so first in config is called first...
            for plugin_class in all_plugin_classes:
                if plugin_name == plugin_class.__name__:
                    self.pm.register(plugin_class(self), plugin_class.__name__)
        self.plugin_setup()

    def load_plugins(self, plugin_folders: list[Path], *, is_external: bool) -> list:
        plugin_classes = []
        with PluginManager.add_to_sys_path(Path("plugins" if is_external else "plugins_builtin")):
            for plugin_path in plugin_folders:
                plugin_class = self.load_plugin(plugin_path, is_external=is_external)
                if plugin_class:
                    plugin_classes.append(plugin_class)
        return plugin_classes

    def load_plugin(self, plugin_path: Path, *, is_external: bool) -> bool:
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
        module_name = plugin_path.name
        try:
            plugin_module = importlib.import_module(module_name)
        except ImportError as e:
            print(e)
            logging.exception("Failed to import module %s", module_name)
            return False
        try:
            plugin_class = plugin_module.PluginMainClass
        except AttributeError:
            logging.exception("Failed to find PluginMainClass in module %s, module will not be loaded!", module_name)
            return False
        if plugin_class.__name__ not in self.plugin_order:
            return False

        # internal plugin dependencies should be handled by the main requirements list, so we only handle
        # dependencies for external plugins!
        if is_external:
            self.handle_dependencies(plugin_module)
        return plugin_class

    def is_installed(self, package_and_version: str) -> bool:
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
            version_specifier = self.convert_caret_to_pip(version_specifier)
            installed_version = parse_version(version(package))
            return installed_version in SpecifierSet(version_specifier)
        except PackageNotFoundError:
            return False

    def install_package(self, package: str) -> bool:
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

    def handle_dependencies(self, plugin_module: any) -> None:
        """
        Handles the dependencies of a plugin module.

        Args:
            plugin_module: The plugin module to handle dependencies for.
        """
        for d in getattr(plugin_module, "dependencies", []):
            if not self.is_installed(d):
                logging.info("Installing package: %s", d)
                self.install_package(d)

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

    def get_all_configured_plugin_names(self) -> list[str]:
        """
        Returns a list of names of all configured plugins.

        Returns:
            list: A list of plugin names.
        """
        names = []
        for p in self.character.plugins:
            names.append(p.name)

        return names

    def get_plugin_config(self, name: str) -> dict:
        """
        Retrieves the configuration for a plugin with the given name.

        Args:
            name (str): The name of the plugin.

        Returns:
            dict or None: The configuration for the plugin if found, None otherwise.
        """
        for p in self.character.plugins:
            if p.name == name:
                if p.config is None:
                    return {}
                return p.config
        return None

    def register_plugin_types(self, plugin_types: list) -> None:
        for plugin_type in plugin_types:
            self.register_plugin_type(plugin_type)

    def plugin_setup(self) -> None:
        """
        Every plugin inplementation should have the plugin_setup method as it could not be called by hooks (because the
        hookspecs would get into the way) we call it directly in the order the plugins where registered
        """
        for plugin in self.pm.get_plugins():
            plugin.plugin_setup()
