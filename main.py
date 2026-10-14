from agent_loop import run_agent
from openai.types.chat import ChatCompletionMessageParam
from session import QueryEngine, list_sessions
from uuid import uuid4
from datetime import datetime
from pathlib import Path
def main(resume_id : str | None = None):
    if resume_id is None:
        session_id = uuid4().hex
    else:
        session_id = resume_id

    session = QueryEngine(
        session_id=session_id,
        session_dir="sessions",
    )

    if resume_id is not None:
        try:
            messages: list[ChatCompletionMessageParam] = session.load_messages(resume_id)
        except FileNotFoundError:
            print(f"Error: No session found with ID {resume_id}.")
            return
    else:
        messages: list[ChatCompletionMessageParam] = [
            {
                "role": "system",
                "content": "You are a helpful assistant that can read and list files in the local directory."
            }
        ]
        session.save_messages(messages)

    print(f"Session ID: {session_id}")
   
    while True:
        user_input = input("User: ")
        if user_input.lower() in ["exit", "quit"]:
            print("Exiting the assistant.")
            break
        if user_input == "/clear":
            del messages[1:]
            session.save_messages(messages)
            print("Conversation history cleared.")
            continue
        if not user_input:
            continue

        messages.append({
            "role": "user",
            "content": user_input
        })
        run_agent(messages)
        session.save_messages(messages)
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--resume", type=str, help="Resume a session with the given session ID.")
    parser.add_argument("--list-sessions", action="store_true", help="List sessions, most recently updated first.")
    args = parser.parse_args()
    if args.list_sessions:
        session_ids = list_sessions("sessions")
        if not session_ids:
            print("还没有保存的会话。")
        else:
            print("已有会话（最近更新的在前）：")
            print("更新时间                   会话ID")
            for session_id in session_ids:
                session_file = Path("sessions") / f"{session_id}_messages.json"
                updated_time = datetime.fromtimestamp(session_file.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
                print(f"{updated_time}    {session_id}")
    else:
        main(resume_id=args.resume)
 
