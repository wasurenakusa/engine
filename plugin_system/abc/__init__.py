from plugin_system.abc.emitter import EmitterPlugin
from plugin_system.abc.llm import LlmPlugin

# from plugin_system.abc.llm_function import LlmFunctionPlugin
from plugin_system.abc.memory import MemoryPlugin
from plugin_system.abc.reciver import ReciverPlugin
from plugin_system.abc.sys_prompt import SystemPromptPlugin
from plugin_system.abc.workflow import WorkflowPlugin

base_plugin_types = [
    SystemPromptPlugin,
    ReciverPlugin,
    EmitterPlugin,
    WorkflowPlugin,
    MemoryPlugin,
    # LlmFunctionPlugin, # Simple way to these plugins for now even if they are implemented the required methods
    LlmPlugin,
]
