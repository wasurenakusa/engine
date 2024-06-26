from plugins_builtin.llm_anthropic.anthropic_llm import AnthropicLlm

dependencies = ["anthropic=^0.29.0"]

PluginMainClass = AnthropicLlm

PLUGIN_NAME = "Anthropic LLM"
PLUGIN_AUTHOR = "wasurenakusa team"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = """Adds handling of anthropics llm models like claude 3."""
