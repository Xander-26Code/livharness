import json
from pathlib import Path
from typing import cast

from tools import tool_functions, tools

from tool_result import ToolError, ToolResult
import os
from dotenv import load_dotenv
from openai import OpenAI
from openai.types.chat import  ChatCompletionToolParam, ChatCompletionMessageParam


load_dotenv(Path(__file__).resolve().parent / ".env", override=True)

client = OpenAI(
    api_key=os.environ["DEEPSEEK_API_KEY"],
    base_url="https://api.deepseek.com")
def run_agent(messages: list[ChatCompletionMessageParam]):
    for step in range(10):
        response = client.chat.completions.create(
        model="deepseek-flash",
        messages=messages,
        tools=tools,
        stream=False,
        extra_body={"thinking": {"type": "disabled"}}
        )
        message = response.choices[0].message

        if message.tool_calls:
            
            # SDK serialization returns a general dict; identify it as a message for type checking.
            assistant_message = cast(ChatCompletionMessageParam, message.model_dump(exclude_none=True))
            messages.append(assistant_message)
            for tool_call in message.tool_calls:
                if tool_call.type != "function":
                    print("暂时不支持非函数调用")
                    return

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
                    result_text = result.to_dict()
                    result = json.dumps(result_text, ensure_ascii=False, indent=2)
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": result
                    })
                    continue
                print(f"[工具调用] {tool_name}，参数：{arguments}")
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
                result_text = result.to_dict()
                result = json.dumps(result_text, ensure_ascii=False, indent=2)
                print(f"[工具结果] {result_text}")
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result
                })
        else:
            messages.append({
                "role": "assistant",
                "content": message.content
            })
            print("assistant:", message.content)
            return
    print("Error: Maximum steps reached without a final response from the assistant.")
