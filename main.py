import json
from typing import cast

from tools.read_file import read_file


import os
from openai import OpenAI
from openai.types.chat import  ChatCompletionToolParam, ChatCompletionMessageParam

tools: list[ChatCompletionToolParam] = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "读取本地文本文件的内容。",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "要读取的文件路径，例如 hello.txt"
                    }
                },
                "required": ["file_path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "列出指定目录下的所有文件。",
            "parameters": {
                "type": "object",
                "properties": {
                    "directory": {
                        "type": "string",
                        "description": "要列出文件的目录路径，例如 ./"
                    }
                },
                "required": ["directory"]
            }
        }
    }
]

tool_functions = {
    "read_file": read_file,
}

client = OpenAI(
    api_key="sk-3813cc314426455098b351633d0024ca",
    base_url="https://api.deepseek.com")



def main():
    messages : list[ChatCompletionMessageParam]=[
            {
                "role": "system",
                "content": "你是一个助手，需要读取文件时请使用工具。"
            },
            {
                "role": "user",
                "content": "请读取 hello.txt，告诉我里面写了什么。"
            }
        ]

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
                arguments = json.loads(tool_call.function.arguments)
                function = tool_functions.get(tool_name)
                if function is None:
                    result = f"Error: Tool '{tool_name}' is not implemented."
                else:
                    try:
                        result = function(**arguments)
                    except TypeError as e:
                        result = f"Error: {str(e)}"
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result
                })
        else:
            print(f"Assistant's response:\n{message.content}")
            return
    print("Error: Maximum steps reached without a final response from the assistant.")
if __name__ == "__main__":
    main()
