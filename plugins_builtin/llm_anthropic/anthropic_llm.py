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
from models.message import FileModel, MessageModel
from models.response import ResponseMessageModel
from models.system_prompt import SystemPrompt
from plugin_system.abc.llm import LlmPlugin
from plugins_builtin.llm_anthropic.prompts import (
    DEFAULT_CHAIN_OF_THOUGHTS_PROMPT,
)


class AnthropicConfigModel(BaseSettings):
    api_key: str = Field(None, alias="ANTHROPIC_API_KEY")  # Set
    model: str = "claude-3-5-sonnet-20240620"
    max_tokens: int = 1000
    temperature: float | None = 1
    image_inclusion_threshold: int = 2
    cot_prompt: str = DEFAULT_CHAIN_OF_THOUGHTS_PROMPT
    max_tool_calls: int = 10
    important_rules_prompt: str | None = None


SUPPORTED_FILE_TYPES = ("image/jpeg", "image/png", "image/gif", "image/webp")


class AnthropicLlm(LlmPlugin):
    config: AnthropicConfigModel

    async def plugin_setup(self) -> None:
        self.load_config(AnthropicConfigModel)
        if self.config.api_key is None:
            msg = "No 'ANTHROPIC_API_KEY' provided in the environment variables or plugin config! Can't continue to \
                initialize the AnthropicLlm plugin!"
            raise ValueError(msg)
        self.client = AsyncAnthropic(api_key=self.config.api_key)

    async def get_llm_response(self, ctx: Context) -> None:
        """
        Generates a response using the Language Learning Model (LLM).

        Args:
            ctx (Context): The context object containing the necessary information for generating the response.

        Returns:
            None
        """
        system_prompts = self.generate_system_prompt(ctx)
        tools, tool_to_fn_map = self.generate_tool_list_and_map(ctx)
        messages = self.generate_message_params_from_memory(ctx)
        # Add the current user message to the messages list
        messages.append({"role": "user", "content": self.engine_content_to_anthropic(ctx.request.content)})

        response_message: anthropic_types.Message
        response_message = await self.generate_response(
            model=self.config.model,
            max_tokens=self.config.max_tokens,
            temperature=self.config.temperature,
            system=system_prompts,
            messages=messages,
            tools=tools,
        )

        if response_message.stop_reason == "tool_use":
            calls = 0
            while response_message.stop_reason == "tool_use" and calls < self.config.max_tool_calls:
                tool_name = response_message.content[0].name
                tool_fn = tool_to_fn_map[tool_name]
                tool_input = response_message.content[0].input
                tool_output = await tool_fn(**tool_input)

                tool_result_message: anthropic_types.ToolResultBlockParam = {
                    "type": "tool_result",
                    "tool_use_id": response_message.content[0].tool_use_id,
                    "content": {
                        "type": "text",
                        "text": tool_output,
                    },
                }
                messages.append(tool_result_message)
                tools_to_use = tools

                # if we run out ouf calls we should not call the tool anymore
                if calls + 1 == self.config.max_tool_calls:
                    tools_to_use = []

                response_message = await self.generate_response(
                    model=self.config.model,
                    max_tokens=self.config.max_tokens,
                    temperature=self.config.temperature,
                    system=system_prompts,
                    messages=messages,
                    tools=tools_to_use,
                )
                calls += 1
        elif response_message.stop_reason in ("end_turn", "max_tokens", "stop_sequence"):
            ctx.response = ResponseMessageModel(role="llm", content=[response_message.content[0].text])
        else:
            ctx.response = ResponseMessageModel(role="llm", content=["..."])

    def generate_system_prompt(self, ctx: Context) -> str:
        final_system_prompt = ""

        for sp in ctx.system_prompts:
            final_system_prompt += ElementTree.tostring(self.system_prompt_to_xml(sp), encoding="unicode") + "\n"

        if len(ctx.llm_functions) != 0:
            # LLM functions are present, we should add the chain of thoughts instructions to the system prompts
            sp = SystemPrompt(
                name="ChainOfThoughts",
                content=self.config.cot_prompt,
            )
            final_system_prompt += (
                ElementTree.tostring(
                    self.system_prompt_to_xml(sp),
                    encoding="unicode",
                )
                + "\n"
            )

        if self.config.important_rules_prompt:
            sp = SystemPrompt(
                name="ImportantRules",
                content=str(self.config.important_rules_prompt),
            )
            final_system_prompt += (
                ElementTree.tostring(
                    self.system_prompt_to_xml(sp),
                    encoding="unicode",
                )
                + "\n"
            )

        return final_system_prompt

    def system_prompt_to_xml(self, system_prompt: SystemPrompt) -> ElementTree.Element:
        """
        Converts a SystemPrompt object to an XML Element.

        Args:
            sp (SystemPrompt): The SystemPrompt object to convert.

        Returns:
            ElementTree.Element: The XML Element representing the SystemPrompt.
        """
        if isinstance(system_prompt.content, SystemPrompt):
            xml = ElementTree.Element(system_prompt.name)
            xml.append(self.system_prompt_to_xml(system_prompt.content))
            return xml
        xml = ElementTree.Element(system_prompt.name)
        xml.text = system_prompt.content
        return xml

    async def generate_response(  # noqa: PLR0913
        self,
        model: str,
        max_tokens: int,
        temperature: float,
        system: str,
        messages: list[anthropic_types.MessageParam],
        tools: list[anthropic_types.ToolParam],
    ) -> anthropic_types.Message:
        """
        Generates a response using the Anthropic Language Model.

        Args:
            system_prompts (str): The system prompts to provide context for the response.
            messages (list[anthropic_types.MessageParam]): The list of messages exchanged between the user
                                                           and the system.
            tools (list[dict]): The list of tools used for generating the response.

        Returns:
            anthropic_types.Message: The generated response message.

        Raises:
            ServerNotReachableError: If there is an API connection error or rate limit reached.
        """
        r: anthropic_types.Message  # Python type hinting... not needed for the code to work but for my sanity...
        try:
            r = await self.client.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                stream=False,  # We dont want to stream the response...
                system=system,
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

    def generate_tool_list_and_map(self, ctx: Context) -> tuple[list[dict], dict]:
        tool_map = {}
        tools = []

        for llm_fn in ctx.llm_functions:
            tool, tool_name, tool_fn = self.engine_llm_function_to_anthropic(llm_fn)
            tool_map[tool_name] = tool_fn
            tools.append(tool)
        return tools, tool_map

    def generate_message_params_from_memory(self, ctx: Context) -> list[anthropic_types.MessageParam]:
        messages = []
        for i, memory_message in enumerate(ctx.shortterm_memory):
            messages.append(self.engine_message_to_anthropic(memory_message, len(ctx.shortterm_memory), i))

        return messages

    def engine_message_to_anthropic(
        self,
        message: MessageModel,
        memories_cnt: int,
        cnt: int,
    ) -> anthropic_types.MessageParam:
        message_param = {}
        if message.role == "user":
            message_param["role"] = "user"
        else:
            message_param["role"] = "assistant"

        message_param["content"] = self.engine_content_to_anthropic(
            message.content,
            exclude_images=memories_cnt - cnt > self.config.image_inclusion_threshold,
        )
        return message_param

    def engine_content_to_anthropic(self, content_list: list[str | FileModel], *, exclude_images: bool = False) -> dict:
        """
        Convert a list of content items to a dictionary representation.

        Args:
            content_list (list[str | FileModel]): The list of content items to convert.
            exclude_images (bool, optional): Whether to exclude images from the conversion. Defaults to False.

        Returns:
            dict: The dictionary representation of the content items.

        Raises:
            None

        """
        res = []
        for c in content_list:
            if isinstance(c, str):
                res.append(
                    {
                        "type": "text",
                        "text": c,
                    },
                )
            elif isinstance(c, FileModel) and exclude_images is False:
                if c.mimetype not in SUPPORTED_FILE_TYPES:
                    # Anthropic only supports images for now so we skip other file types
                    continue
                res.append(
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "data": base64.b64encode(c.data),
                            "media_type": c.mimetype,
                        },
                    },
                )
        return res

    def engine_llm_function_to_anthropic(self, llm_fn: LlmFunction) -> tuple[anthropic_types.ToolParam, str, callable]:
        """
        Converts an LlmFunction object to a tool dictionary, tool name, and callable function.

        Args:
            llm_fn (LlmFunction): The LlmFunction object to convert.

        Returns:
            tuple[anthropic_types.ToolParam, str, callable]: A tuple containing the tool dictionary,
            tool name, and callable function.

        """
        # we generate a random name for the tool to ensure that it is unique, 8 characters should be enough
        tool_name = "".join(random.choices(string.ascii_lowercase, k=8))  # noqa: S311 No crypto in this case
        tool_input_schema = {
            "type": "object",
            "properties": {},
            "required": [],
        }
        tool_dict: anthropic_types.ToolParam = {
            "name": tool_name,
            "description": llm_fn.description,
            "input_schema": tool_input_schema,
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
