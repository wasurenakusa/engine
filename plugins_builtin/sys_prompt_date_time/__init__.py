from .date_time import DateTimePlugin

dependencies = ["pendulum==^3.0.0", "httpx=^0.27.0"]

PluginMainClass = DateTimePlugin

PLUGIN_NAME = "DateTime Prompt Plugin"
PLUGIN_AUTHOR = "wasurenakusa team"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "Configurable time return prompt"
