import base64
import random
import string
from xml.etree import ElementTree

from anthropic import APIConnectionError, APIStatusError, AsyncAnthropic, RateLimitError
from anthropic import types as anthropic_types
from pydantic import Field
from pydantic_settings import BaseSettings

from models.context import Context
from models.llm_function import LlmFunction
from models.message import FileModel
from models.response import ResponseMessageModel
from models.system_prompt import SystemPrompt
from plugin_system.abc.llm import LlmPlugin
from plugins_builtin.llm_anthropic.prompts import (
    DEFAULT_CHAIN_OF_THOUGHTS_PROMPT,
    DEFAULT_CHAIN_OF_THOUGHTS_THINKING_TAG,
)


class AnthropicConfigModel(BaseSettings):
    api_key: str = Field(None, alias="ANTHROPIC_API_KEY")  # Set
    model: str = "claude-3-5-sonnet-20240620"
    max_tokens: int = 1000
    temperature: float | None = 1
    top_p: float | None = None  # Set temperature to None to use top_p and top_k
    top_k: int | None = None
    include_image_for_the_last_n: int = 2
    chain_of_thoughts_prompt: str = DEFAULT_CHAIN_OF_THOUGHTS_PROMPT
    chain_of_thoughts_thinking_tag: str = DEFAULT_CHAIN_OF_THOUGHTS_THINKING_TAG
    max_tool_calls: int = 10


SUPPORTED_FILE_TYPES = ("image/jpeg", "image/png", "image/gif", "image/webp")


class AnthropicLlm(LlmPlugin):
    config: AnthropicConfigModel

    async def plugin_setup(self) -> None:
        config = self.pm.get_plugin_config(self.__class__.__name__)
        self.config = AnthropicConfigModel(**config)
        if self.config.api_key is None:
            msg = "No 'ANTHROPIC_API_KEY' provided in the environment variables or plugin config! Can't continue to \
                initialize the AnthropicLlm plugin!"
            raise ValueError(msg)
        self.client = AsyncAnthropic(api_key=self.config.api_key)

    def system_prompt_to_xml(self, sp: SystemPrompt) -> ElementTree.Element:
        if isinstance(sp.content, SystemPrompt):
            return ElementTree.Element(sp.name, self.system_prompt_to_xml(sp.content))
        return ElementTree.Element(sp.name, sp.content)

    async def get_llm_response(self, ctx: Context) -> None:
        system_prompts = ""

        for sp in ctx.system_prompts:
            system_prompts += ElementTree.tostring(self.system_prompt_to_xml(sp), encoding="unicode")

        if len(ctx.llm_functions) != 0:
            # LLM functions are present, we should add the chain of thoughts instructions to the system prompts
            system_prompts += ElementTree.tostring(
                self.system_prompt_to_xml(SystemPrompt(name="chain_of_thoughts")),
                encoding="unicode",
            )

        messages = self.shortterm_memory_to_message_param(ctx)
        tools, tool_to_fn_map = self.llm_functions_to_tool_dict(ctx)

        message: anthropic_types.Message
        message = await self.generate_response(
            model=self.config.model,
            max_tokens=self.config.max_tokens,
            temperature=self.config.temperature,
            top_p=self.config.top_p,
            top_k=self.config.top_k,
            stream=False,
            system=system_prompts,
            messages=messages,
            tools=tools,
        )

        if message.stop_reason == "tool_use":
            calls = 0
            while message.stop_reason == "tool_use" and calls < self.config.max_tool_calls:
                tool_name = message.content[0].name
                tool_fn = tool_to_fn_map[tool_name]
                tool_input = message.content[0].input
                tool_output = tool_fn(**tool_input)

                tool_result_message: anthropic_types.ToolResultBlockParam = {
                    "type": "tool_result",
                    "tool_use_id": message.content[0].tool_use_id,
                    "content": {
                        "type": "text",
                        "text": tool_output,
                    },
                }
                messages.append(tool_result_message)
                message = await self.generate_response(
                    model=self.config.model,
                    max_tokens=self.config.max_tokens,
                    temperature=self.config.temperature,
                    top_p=self.config.top_p,
                    top_k=self.config.top_k,
                    stream=False,
                    system=system_prompts,
                    messages=messages,
                    tools=tools,
                )
                calls += 1

            pass
        elif message.stop_reason in ("end_turn", "max_tokens", "stop_sequence"):
            content = message.content[0].text
            ctx.response = ResponseMessageModel(role="llm", content=[content])
            return

    async def generate_response(
        self,
        system_prompts: str,
        messages: list[anthropic_types.MessageParam],
        tools: list[dict],
    ) -> anthropic_types.Message:
        r: anthropic_types.Message  # Python type hinting... not needed for the code to work but for my sanity...
        try:
            r = await self.client.messages.create(
                model=self.config.model,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
                top_p=self.config.top_p,
                top_k=self.config.top_k,
                stream=False,  # We dont want to stream the response...
                system=system_prompts,
                messages=messages,
                tools=tools,
            )
        except APIConnectionError as e:
            self.logger.exception("API connection error!")
            raise self.ServerNotReachableError() from e
        except RateLimitError as e:
            # We can't do anything about it, so we just raise it like its a server not reachable error (so other LLM
            # plugins can take over)
            self.logger.warning("Rate limit reached!")
            raise self.ServerNotReachableError() from e
        except APIStatusError as e:
            self.logger.exception("API status error!")
            raise self.ServerNotReachableError() from e
        return r

    def llm_functions_to_tool_dict(self, ctx: Context) -> tuple[list[dict], dict]:
        tool_map = {}
        tools = []

        for llm_fn in ctx.llm_functions:
            tool, tool_name, tool_fn = self.parse_llm_function_to_tool(llm_fn)
            tool_map[tool_name] = tool_fn
            tools.append(tool)
        return tools, tool_map

    def shortterm_memory_to_message_param(self, ctx: Context) -> list[anthropic_types.MessageParam]:
        messages = []

        memory_length = len(ctx.shortterm_memory)
        for i, memory in enumerate(ctx.shortterm_memory):
            mp = {}
            if memory.role == "user":
                mp["role"] = "user"
            else:
                mp["role"] = "assistant"

            exclude_images = memory_length - i > self.config.include_image_for_the_last_n
            mp["content"] = self.content_to_dict(
                memory,
                exclude_images=exclude_images,
            )
            messages.append(mp)

        messages.append({"role": "user", "content": self.content_to_dict(ctx.request.content)})
        return messages

    def content_to_dict(self, content_list: list[str | FileModel], *, exclude_images: bool = False) -> dict:
        res = []
        for c in content_list:
            if isinstance(c, str):
                res["content"].append(
                    {
                        "type": "text",
                        "data": c,
                    },
                )
            elif isinstance(c, FileModel) and exclude_images is False:
                if c.mimetype not in SUPPORTED_FILE_TYPES:
                    # Anthropic only supports images for now so we skip other file types
                    continue
                res["content"] = {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "data": base64.b64encode(c.data),
                        "media_type": c.mimetype,
                    },
                }
        return res

    def parse_llm_function_to_tool(self, llm_fn: LlmFunction) -> tuple[dict, str, callable]:
        # we generate a random name for the tool to ensure that it is unique, 8 characters should be enough
        tool_name = "".join(random.choices(string.ascii_lowercase, k=8))  # noqa: S311 No crypto in this case
        tool_dict = {
            "name": tool_name,
            "description": llm_fn.description,
            "input_schema": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        }
        for param in llm_fn.parameters:
            tool_dict["input_schema"]["properties"][param.name] = {
                "type": param.parameter_type,
                "description": param.description,
            }
            if param.required:
                tool_dict["input_schema"]["required"].append(param.name)
        if len(tool_dict["input_schema"]["required"]) == 0:
            del tool_dict["input_schema"]["required"]

        return tool_dict, tool_name, llm_fn.fn
