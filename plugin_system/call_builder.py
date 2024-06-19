import random


class CallBuilder:
    def __init__(self, plugin_map: dict[str, list[type]], function_name: str, **kwargs: dict[str, any]) -> None:
        self.function_name = function_name
        self.plugin_list = plugin_map.get(self.function_name)
        if not self.plugin_list:
            self.plugin_list = []
        self.kwargs = kwargs

    def all(self) -> list[any]:
        results = []
        for plugin in self.plugin_list:
            results.append(getattr(plugin, self.function_name)(**self.kwargs))
        return results

    def first(self) -> list[any]:
        if not self.plugin_list:
            return []
        return [getattr(self.plugin_list[0], self.function_name)(**self.kwargs)]

    def last(self) -> list[any]:
        if not self.plugin_list:
            return []
        return [getattr(self.plugin_list[-1], self.function_name)(**self.kwargs)]

    def random(self) -> list[any]:
        if not self.plugin_list:
            return []
        rng = random.randint(0, len(self.plugin_list) - 1)  # noqa: S311  No shite, Sherlock
        return [getattr(self.plugin_list[rng], self.function_name)(**self.kwargs)]
