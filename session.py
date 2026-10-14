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
