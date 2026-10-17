import json
from pathlib import Path
from openai.types.chat import ChatCompletionMessageParam
from file_io import atomic_write_text


def validate_session_id(session_id: str) -> None:
    if not isinstance(session_id, str) or not session_id.isascii() or not session_id.replace("_", "").replace("-", "").isalnum():
        raise ValueError("Session IDs may contain only ASCII letters, digits, underscores, and hyphens.")


def validate_messages(messages: object) -> None:
    """本项目只保存文本消息；损坏的历史应在恢复前报错。"""
    if not isinstance(messages, list):
        raise ValueError("Session messages must be a list.")
    pending: set[str] = set()
    seen: set[str] = set()
    for message in messages:
        if not isinstance(message, dict) or message.get("role") not in ("system", "user", "assistant", "tool"):
            raise ValueError("Invalid message role in session.")
        role = message["role"]
        content = message.get("content")
        if not isinstance(content, str) and not (role == "assistant" and content is None):
            raise ValueError("Session message content must be text.")
        if pending and role != "tool":
            raise ValueError("Session has missing tool results before another message.")
        if role == "assistant":
            if not isinstance(message.get("reasoning_content", ""), str):
                raise ValueError("Invalid reasoning content in session.")
            calls = message.get("tool_calls")
            if calls is None:
                calls = []
            if not isinstance(calls, list):
                raise ValueError("Session tool_calls must be a list.")
            for call in calls:
                if not isinstance(call, dict) or call.get("type") != "function":
                    raise ValueError("Invalid tool call in session.")
                call_id = call.get("id")
                function = call.get("function")
                if not isinstance(call_id, str) or not call_id or call_id in seen:
                    raise ValueError("Missing or duplicate tool call ID in session.")
                if not isinstance(function, dict) or not isinstance(function.get("name"), str) or not function["name"] or not isinstance(function.get("arguments"), str):
                    raise ValueError("Invalid tool function in session.")
                seen.add(call_id)
                pending.add(call_id)
        elif role == "tool":
            call_id = message.get("tool_call_id")
            if not isinstance(call_id, str) or call_id not in pending:
                raise ValueError("Tool result has no matching pending call in session.")
            pending.remove(call_id)
    # 文件末尾的未完成工具调用由界面标记为 interrupted，不重新执行。


class QueryEngine:
    def __init__(self, session_id: str, session_dir: str):
        validate_session_id(session_id)
        self.session_id = session_id
        self.session_dir = Path(session_dir)

    def save_messages(self, messages: list[ChatCompletionMessageParam]):
        self.session_dir.mkdir(parents=True, exist_ok=True)
        content = json.dumps(messages, ensure_ascii=False, indent=4)
        atomic_write_text(self.session_dir / f"{self.session_id}_messages.json", content)

    def load_messages(self, session_id: str) -> list[ChatCompletionMessageParam]:
        validate_session_id(session_id)
        with open(self.session_dir / f"{session_id}_messages.json", "r", encoding="utf-8") as f:
            messages = json.load(f)
        validate_messages(messages)
        return messages


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
