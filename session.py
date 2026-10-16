import json
from pathlib import Path
from openai.types.chat import ChatCompletionMessageParam
class QueryEngine:
    def __init__(self, session_id: str, session_dir: str):
        self.session_id = session_id
        self.session_dir = Path(session_dir)

    def save_messages(self, messages: list[ChatCompletionMessageParam]):
        self.session_dir.mkdir(parents=True, exist_ok=True)
        with open(self.session_dir / f"{self.session_id}_messages.json", "w", encoding="utf-8") as f:
            json.dump(messages, f, ensure_ascii=False, indent=4)

    def load_messages(self, session_id: str) -> list[ChatCompletionMessageParam]:
        with open(self.session_dir / f"{session_id}_messages.json", "r", encoding="utf-8") as f:
            return json.load(f)


def get_updated_time(file: Path) -> float:
    return file.stat().st_mtime


def list_sessions(session_dir: str) -> list[str]:
    directory = Path(session_dir)
    files = [file for file in directory.glob("*_messages.json") if file.is_file()]
    files.sort(key=get_updated_time, reverse=True)

    session_ids = []
    for file in files:
        session_ids.append(file.name.removesuffix("_messages.json"))
    return session_ids

def get_session_title(messages: list[ChatCompletionMessageParam]) -> str:
    for message in messages:
        if message["role"] != "user":
            continue

        content = message.get("content")
        if not isinstance(content, str):
            continue

        title = " ".join(content.split())

        if not title:
            continue

        if len(title) > 30:
            return title[:30] + "..."

        return title
    return "New conversation"
