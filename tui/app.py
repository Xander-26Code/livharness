"""把用户输入、Agent 回调和会话保存连接起来。"""

import json
import time
from uuid import uuid4

from openai import APIConnectionError, APIStatusError, AuthenticationError
from openai.types.chat import ChatCompletionMessageParam

from agent_loop import MAX_STEPS, MODEL, run_agent
from session import QueryEngine, list_sessions
from tool_result import ToolError, ToolResult
from tui.input import TerminalInput
from tui.render import TerminalUI

SYSTEM_MESSAGE: ChatCompletionMessageParam = {
    "role": "system",
    "content": "You are a helpful assistant that can read and list files in the local directory.",
}


def close_pending_tools(messages: list[ChatCompletionMessageParam]) -> None:
    """中断后补全缺失的工具结果，不把未知的执行结果当成成功。"""
    pending = {}
    for message in messages:
        if message["role"] == "assistant":
            for call in message.get("tool_calls", []):
                if call["type"] == "function":
                    pending[call["id"]] = call["function"]["name"]
        elif message["role"] == "tool":
            pending.pop(message["tool_call_id"], None)
    for call_id, tool in pending.items():
        result = ToolResult(
            tool=tool, status="error", summary="Execution interrupted; outcome unknown",
            data={}, error=ToolError(
                code="EXECUTION_INTERRUPTED",
                message="No result was recorded. The tool may or may not have run. Inspect the current state before retrying any changes.",
                retryable=False,
            ),
        )
        messages.append({"role": "tool", "tool_call_id": call_id, "content": json.dumps(result.to_dict(), ensure_ascii=False)})


def open_session(session_id: str | None, directory: str):
    if session_id is not None and (not session_id.isascii() or not session_id.replace("_", "").replace("-", "").isalnum()):
        raise ValueError("Session IDs may contain only ASCII letters, digits, underscores, and hyphens.")
    session = QueryEngine(session_id=session_id or uuid4().hex, session_dir=directory)
    if session_id:
        messages = session.load_messages(session_id)
        if not isinstance(messages, list) or not all(isinstance(item, dict) and "role" in item for item in messages):
            raise ValueError("Invalid message format in the session file.")
        close_pending_tools(messages)
    else:
        messages = [SYSTEM_MESSAGE.copy()]
        session.save_messages(messages)
    return session, messages


def save_session(session: QueryEngine, messages: list, ui: TerminalUI) -> bool:
    try:
        session.save_messages(messages)
        return True
    except OSError as exc:
        ui.notice(f"Could not save: {exc}. The conversation is still in memory. Check directory permissions before continuing.", "bad")
        return False


def resolve_resume_id(value: str, displayed_ids: list[str]) -> str:
    """编号只查最近一次展示的列表，不重新排序；32位数字 ID 仍按 ID 处理。"""
    if value.isascii() and value.isdigit() and len(value) < 32:
        if not displayed_ids:
            raise ValueError("Use /sessions first, then /resume NUMBER to choose a session.")
        index = int(value) - 1
        if not 0 <= index < len(displayed_ids):
            raise ValueError(f"Choose a number from 1 to {len(displayed_ids)}, or use /sessions to refresh.")
        return displayed_ids[index]
    return value


def run_app(resume_id: str | None = None, plain: bool = False, session_dir: str = "sessions") -> None:
    ui = TerminalUI(plain=plain)
    try:
        session, messages = open_session(resume_id, session_dir)
    except (OSError, ValueError) as exc:
        ui.notice(f"Could not open session: {exc}", "bad")
        return
    reader = TerminalInput(plain=plain)
    reader.set_history(messages)
    ui.welcome(session.session_id, MODEL, resumed=resume_id is not None)
    if resume_id:
        ui.history(messages)
    displayed_session_ids: list[str] = []

    while True:
        try:
            text = reader.read(session.session_id).strip()
        except KeyboardInterrupt:
            ui.notice("Input cancelled. Use /exit to quit.")
            continue
        except EOFError:
            if save_session(session, messages, ui):
                ui.notice("Session saved. Goodbye.")
            return
        if not text:
            continue
        if text.lower() in ("exit", "quit", "/exit", "/quit"):
            if save_session(session, messages, ui):
                ui.notice("Session saved. Goodbye.")
                return
            continue
        if text.startswith("/"):
            command, _, argument = text.partition(" ")
            try:
                if command == "/help":
                    ui.help()
                elif command == "/session":
                    ui.notice(f"Session ID: {session.session_id}")
                elif command == "/sessions" or (command == "/resume" and not argument.strip()):
                    displayed_session_ids = list_sessions(session_dir)
                    ui.sessions(displayed_session_ids, session_dir, selectable=True)
                elif command == "/details":
                    ui.details = not ui.details
                    ui.notice(f"Tool details {'enabled' if ui.details else 'disabled'} for subsequent calls.")
                elif command == "/clear":
                    del messages[1:]
                    save_session(session, messages, ui)
                    reader.set_history(messages)
                    ui.notice("Conversation context cleared. File changes are unchanged.")
                elif command in ("/new", "/resume"):
                    new_id = resolve_resume_id(argument.strip(), displayed_session_ids) if command == "/resume" else None
                    if not save_session(session, messages, ui):
                        continue
                    session, messages = open_session(new_id, session_dir)
                    reader.set_history(messages)
                    ui.welcome(session.session_id, MODEL, resumed=new_id is not None)
                    if new_id:
                        ui.history(messages)
                else:
                    ui.notice("Unknown command. Use /help to see available commands.", "warn")
            except (OSError, ValueError) as exc:
                ui.notice(f"Could not complete the operation: {exc}", "bad")
            continue

        ui.user(text)
        messages.append({"role": "user", "content": text})
        started = time.monotonic()
        status = "error"
        error = None
        try:
            with ui.working():
                status = run_agent(messages, on_response=ui.response, on_event=ui.event)
        except KeyboardInterrupt:
            status = "interrupted"
            close_pending_tools(messages)
        except AuthenticationError:
            error = "Authentication failed. Check DEEPSEEK_API_KEY in .env and restart the app."
        except APIConnectionError:
            error = "Could not connect to the model. Check your network and try again."
        except APIStatusError as exc:
            error = f"The model service returned HTTP {exc.status_code}. This turn has stopped."
        except Exception as exc:
            error = f"Execution failed ({type(exc).__name__}): {exc}"
        if error:
            close_pending_tools(messages)
            ui.notice(error, "bad")
        save_session(session, messages, ui)
        if status == "max_steps":
            ui.notice(f"Reached the {MAX_STEPS}-request limit for this turn. The task may be unfinished. Enter a new instruction to continue.", "warn")
        elif status == "interrupted":
            ui.notice("Turn stopped. File changes are not undone. Check tools with missing results before retrying.", "warn")
        elif status == "unsupported_tool":
            ui.notice("The model requested an unsupported tool type. This turn has stopped.", "warn")
        ui.turn_end(time.monotonic() - started)
