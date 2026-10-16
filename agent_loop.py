import json
from pathlib import Path
from typing import cast, Callable

from tools import tool_functions, tools

from tool_result import ToolError, ToolResult
import os
from dotenv import load_dotenv
from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam, ChatCompletionMessage


MODEL = "deepseek-flash"
MAX_STEPS = 10
client: OpenAI | None = None


def get_client() -> OpenAI:
    """只在发送模型请求时读取配置，帮助、预览和会话列表可以离线使用。"""
    global client
    if client is None:
        load_dotenv(Path(__file__).resolve().parent / ".env", override=True)
        api_key = os.environ.get("DEEPSEEK_API_KEY")
        if not api_key:
            raise ValueError("Set DEEPSEEK_API_KEY in the project .env file before sending a message.")
        client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
    return client


def run_agent(
    messages: list[ChatCompletionMessageParam],
    on_response: Callable[[str], None] = print,
    on_event: Callable[[str, dict], None] | None = None,
) -> str:
    """修改同一份 messages；通过回调传递展示内容，返回本轮停止原因。"""
    def emit(event: str, data: dict) -> None:
        if on_event is not None:
            on_event(event, data)
        elif event == "tool_start":
            print(f"[Tool call] {data['tool']}, arguments: {data['arguments']}")
        elif event == "tool_result":
            print(f"[Tool result] {data}")

    def record_result(call_id: str, result: ToolResult) -> None:
        result_dict = result.to_dict()
        messages.append({
            "role": "tool",
            "tool_call_id": call_id,
            "content": json.dumps(result_dict, ensure_ascii=False, indent=2),
        })
        emit("tool_result", result_dict)

    api = get_client()
    for step in range(MAX_STEPS):
        emit("model_start", {"step": step + 1, "max_steps": MAX_STEPS})
        stream = api.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=tools,
            stream=True,
            extra_body={"thinking": {"type": "enabled"}},
        )

        content = ""
        reasoning_content = ""
        finish_reason: str | None = None
        tool_calls: dict[int, dict] = {}
        with stream:
            for chunk in stream:
                if not chunk.choices:
                    continue
                choice = chunk.choices[0]
                delta = choice.delta
                if choice.finish_reason is not None:
                    finish_reason = choice.finish_reason

                reasoning_part = getattr(delta, "reasoning_content", None)
                if reasoning_part:
                    reasoning_content += reasoning_part

                if delta.content:
                    content += delta.content
                    emit("text_delta", {"text": delta.content})

                if delta.tool_calls:
                    for part in delta.tool_calls:
                        if part.index not in tool_calls:
                            tool_calls[part.index] = {
                                "id": "",
                                "type": "function",
                                "function": {
                                    "name": "",
                                    "arguments": "",
                                },
                            }
                        call = tool_calls[part.index]
                        if part.id:
                            call["id"] = part.id

                        if part.function:
                            if part.function.name:
                                call["function"]["name"] = part.function.name
                            if part.function.arguments:
                                call["function"]["arguments"] += part.function.arguments

        if tool_calls:
            expected_reason = "tool_calls"
        else:
            expected_reason = "stop"
        if finish_reason != expected_reason:
            raise RuntimeError(f"Unexpected finish reason: {finish_reason}, expected: {expected_reason}")
        message = ChatCompletionMessage.model_validate(
            {
                "role": "assistant",
                "content": content,
                "reasoning_content": reasoning_content,
                "tool_calls": list(tool_calls.values()) or None,
            }
        )
        emit("model_end", {"has_tool_calls": bool(message.tool_calls)})
        if message.tool_calls:
            # 不写入不支持的工具请求，避免留下没有结果的请求。
            if any(call.type != "function" for call in message.tool_calls):
                return "unsupported_tool"
            # SDK serialization returns a general dict; identify it as a message for type checking.
            assistant_message = cast(ChatCompletionMessageParam, message.model_dump(exclude_none=True))
            messages.append(assistant_message)
            for tool_call in message.tool_calls:
                if tool_call.type != "function":
                    return "unsupported_tool"

                tool_name = tool_call.function.name
                try:
                    arguments = json.loads(tool_call.function.arguments)
                except json.JSONDecodeError:
                    result = ToolResult(
                        tool=tool_name,
                        status="error",
                        summary="Invalid JSON arguments",
                        data={},
                        error=ToolError(
                            code="INVALID_JSON_ARGUMENTS",
                            message=f"The arguments for tool '{tool_name}' are not valid JSON.",
                            retryable=False
                        ),
                    )
                    record_result(tool_call.id, result)
                    continue
                emit("tool_start", {"tool": tool_name, "arguments": arguments})
                function = tool_functions.get(tool_name)
                if function is None:
                    result = ToolResult(
                        tool=tool_name,
                        status="error",
                        summary="Tool not found",
                        data={},
                        error=ToolError(
                            code="TOOL_NOT_FOUND",
                            message=f"The tool '{tool_name}' was not found.",
                            retryable=False
                        ),
                    )
                else:
                    try:
                        result = function(**arguments)
                    except TypeError as e:
                        result = ToolResult(
                            tool=tool_name,
                            status="error",
                            summary="Tool call raised a TypeError",
                            data={},
                            error=ToolError(
                                code="TOOL_TYPE_ERROR",
                                message=f"Tool '{tool_name}' raised TypeError: {e}",
                                retryable=False
                            ),
                        )
                record_result(tool_call.id, result)
        else:
            assistant_message = cast(ChatCompletionMessageParam, message.model_dump(exclude_none=True))
            messages.append(assistant_message)
            on_response(message.content or "")
            return "completed"
    return "max_steps"
