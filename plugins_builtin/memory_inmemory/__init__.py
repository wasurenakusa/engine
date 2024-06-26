from .inmemory import InmemoryPlugin

dependencies = []

PluginMainClass = InmemoryPlugin

PLUGIN_NAME = "Inmemory Memory"
PLUGIN_AUTHOR = "wasurenakusa team"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = """
    Simple memory plugin that stores data in memory and is lost on engine restart. Should only be \
    used for testing when no other memory plugin is availabl and you don't want to store data at all.
    """
