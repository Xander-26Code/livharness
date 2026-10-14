from agent_loop import run_agent
from openai.types.chat import ChatCompletionMessageParam
def main():
    messages: list[ChatCompletionMessageParam] = [
        {
            "role": "system",
            "content": "你是一个助手，需要读取文件时请使用工具。"
        },
    ]

    user_input = input("请输入你的问题：")

    messages.append({
        "role": "user",
        "content": user_input
    })

    run_agent(messages)
if __name__ == "__main__":
    main()
