import random
from collections.abc import Callable

import anyio

from utilities.logging import get_logger


class CallBuilder:
    """
    A class that builds and executes function calls on plugins.

    Attributes:
        function_name (str): The name of the function to be called.
        plugin_list (list[type]): A list of plugin types.
        kwargs (dict[str, any]): Additional keyword arguments to be passed to the function.
    """

    def __init__(self, plugin_map: dict[str, list[type]], function_name: str, **kwargs: dict[str, any]) -> None:
        """
        Initializes a CallBuilder object.

        Args:
            plugin_map (dict[str, list[type]]): A dictionary mapping function names to a list of plugin types.
            function_name (str): The name of the function to be called.
            **kwargs (dict[str, any]): Additional keyword arguments to be passed to the function.

        Returns:
            None
        """
        self.logger = get_logger(__name__)
        self.function_name = function_name
        self.plugin_list = plugin_map.get(self.function_name)
        if not self.plugin_list:
            self.plugin_list = []
        self.kwargs = kwargs

    async def all(self, limit: int | None = None) -> list[any]:
        """
        Executes the specified function on all plugins in the plugin list.

        Args:
            limit (int | None, optional): The maximum number of plugins to execute the function on.
                                         If None, all plugins will be executed. Defaults to None.

        Returns:
            list[any]: A list of results returned by executing the function on each plugin.
        """
        results = []
        plugin_list = self.plugin_list if limit is None else self.plugin_list[:limit]

        if not self.plugin_list:
            self.logger.warning("No plugin function was called for %s", self.function_name)
            return []
        for plugin in plugin_list:
            fn = getattr(plugin, self.function_name)
            result = await fn(**self.kwargs)
            results.append(result)
        self.logger.debug(
            "Called '%s' for %s",
            self.function_name,
            [plugin.__class__.__name__ for plugin in plugin_list],
        )
        return results

    async def first(self) -> list[any]:
        """
        Returns the result of calling the specified function on the first plugin in the plugin list.

        If the plugin list is empty, an empty list is returned.

        Returns:
            list[any]: The result of calling the function on the first plugin.
        """
        if not self.plugin_list:
            return []

        fn = getattr(self.plugin_list[0], self.function_name)
        result = await fn(**self.kwargs)
        return [result]

    async def last(self) -> list[any]:
        """
        Returns the result of calling the last plugin in the plugin list with the specified function name and arguments.

        Returns:
            list[any]: The result of calling the last plugin's function with the specified arguments.
        """
        if not self.plugin_list:
            return []

        fn = getattr(self.plugin_list[-1], self.function_name)
        result = await fn(**self.kwargs)
        return [result]

    async def random(self) -> list[any]:
        """
        Returns a list containing the result of calling a random plugin function.

        If the plugin list is empty, an empty list is returned.

        Returns:
            list[any]: A list containing the result of calling a random plugin function.
        """
        if not self.plugin_list:
            self.logger.warning("No plugin function was called for %s", self._function_name)
            return []

        rng = random.randint(0, len(self.plugin_list) - 1)  # noqa: S311  No shite, Sherlock
        fn = getattr(self.plugin_list[rng], self.function_name)
        result = await fn(**self.kwargs)
        return [result]

    async def only(self, plugins: list[str]) -> list[any]:
        """
        Executes the specified function on the selected plugins only.

        Args:
            plugins (list[str]): A list of plugin names to execute the function on.

        Returns:
            list[any]: A list of results returned by the executed function on the selected plugins.
        """
        results = []
        plugins_called = []
        for plugin in self.plugin_list:
            if plugin.__name__ in plugins:
                fn = getattr(plugin, self.function_name)
                result = await fn(**self.kwargs)
                results.append(result)
                plugins_called.append(plugin.__class__.__name__)
        self.logger.debug(
            "Called '%s' for %s",
            self.function_name,
            plugins_called,
        )
        return results

    async def all_async(self, limit: int | None = None) -> list[any]:
        """
        Executes the specified function on all plugins in the plugin list asyncron. Should only be used if there is no
        ctx changing inside the functions involved otherwise this would most likeley break thinks...
        functions that should be safe: generate_system_prompts, plugin_setup as they dont use the context or respond
        with a not none result.

        Args:
            limit (int | None, optional): The maximum number of plugins to execute the function on.
                                         If None, all plugins will be executed. Defaults to None.

        Returns:
            list[any]: A list of results returned by executing the function on each plugin.
        """

        if not self.plugin_list:
            self.logger.warning("No plugin function was called for %s", self.function_name)
            return []

        results = []
        plugin_list = self.plugin_list if limit is None else self.plugin_list[:limit]

        async def run_and_collect_result(fn: Callable) -> None:
            result = await fn(**self.kwargs)
            results.append(result)

        async with anyio.create_task_group() as tg:
            for plugin in plugin_list:
                fn = getattr(plugin, self.function_name)
                tg.start_soon(run_and_collect_result, fn)

        self.logger.debug(
            "Called '%s' for %s in parallel",
            self.function_name,
            [plugin.__class__.__name__ for plugin in plugin_list],
        )
        return results

    def get_plugin_names(self, plugin_list: list[type]) -> list[str]:
        return [plugin.__class__.__name__ for plugin in plugin_list]
