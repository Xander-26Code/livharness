import json
from pathlib import Path
from typing import cast

from tools import tool_functions, tools


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
                arguments = json.loads(tool_call.function.arguments)
                print("调用工具：", tool_name, "参数：", arguments)
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
