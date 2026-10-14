from agent_loop import run_agent
from openai.types.chat import ChatCompletionMessageParam
from session import QueryEngine
def main():
    messages: list[ChatCompletionMessageParam] = [
        {
            "role": "system",
            "content": "你是一个助手，需要读取文件时请使用工具。"
        },
    ]
    while True:
        user_input = input("User: ")
        if user_input.lower() in ["exit", "quit"]:
            print("Exiting the assistant.")
            break
        if user_input == "/clear":
            del messages[1:]
            print("Conversation history cleared.")
            continue
        if not user_input:
            continue

        messages.append({
            "role": "user",
            "content": user_input
        })
        run_agent(messages)
        QueryEngine(session_id="session_1", session_dir="sessions").save_messages(messages)
if __name__ == "__main__":
    main()
