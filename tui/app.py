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
        raise ValueError("会话 ID 只能包含英文字母、数字、下划线和连字符。")
    session = QueryEngine(session_id=session_id or uuid4().hex, session_dir=directory)
    if session_id:
        messages = session.load_messages(session_id)
        if not isinstance(messages, list) or not all(isinstance(item, dict) and "role" in item for item in messages):
            raise ValueError("会话文件中的消息格式不正确。")
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
        ui.notice(f"保存失败：{exc}。对话仍在内存中，请修复目录权限后再继续。", "bad")
        return False


def run_app(resume_id: str | None = None, plain: bool = False, session_dir: str = "sessions") -> None:
    ui = TerminalUI(plain=plain)
    try:
        session, messages = open_session(resume_id, session_dir)
    except (OSError, ValueError) as exc:
        ui.notice(f"无法打开会话：{exc}", "bad")
        return
    reader = TerminalInput(plain=plain)
    reader.set_history(messages)
    ui.welcome(session.session_id, MODEL, resumed=resume_id is not None)
    if resume_id:
        ui.history(messages)

    while True:
        try:
            text = reader.read(session.session_id).strip()
        except KeyboardInterrupt:
            ui.notice("输入已取消。输入 /exit 退出。")
            continue
        except EOFError:
            if save_session(session, messages, ui):
                ui.notice("会话已保存，再见。")
            return
        if not text:
            continue
        if text.lower() in ("exit", "quit", "/exit", "/quit"):
            if save_session(session, messages, ui):
                ui.notice("会话已保存，再见。")
                return
            continue
        if text.startswith("/"):
            command, _, argument = text.partition(" ")
            try:
                if command == "/help":
                    ui.help()
                elif command == "/session":
                    ui.notice(f"Session ID: {session.session_id}")
                elif command == "/sessions":
                    ui.sessions(list_sessions(session_dir), session_dir)
                elif command == "/details":
                    ui.details = not ui.details
                    ui.notice(f"工具详情已{'开启' if ui.details else '关闭'}，从下一次工具调用生效。")
                elif command == "/clear":
                    del messages[1:]
                    save_session(session, messages, ui)
                    reader.set_history(messages)
                    ui.notice("对话上下文已清空，文件修改保持不变。")
                elif command in ("/new", "/resume"):
                    if command == "/resume" and not argument.strip():
                        ui.notice("用法：/resume 会话ID。可先用 /sessions 查看。", "warn")
                        continue
                    if not save_session(session, messages, ui):
                        continue
                    new_id = argument.strip() if command == "/resume" else None
                    session, messages = open_session(new_id, session_dir)
                    reader.set_history(messages)
                    ui.welcome(session.session_id, MODEL, resumed=new_id is not None)
                    if new_id:
                        ui.history(messages)
                else:
                    ui.notice("未知命令，输入 /help 查看可用命令。", "warn")
            except (OSError, ValueError) as exc:
                ui.notice(f"操作未完成：{exc}", "bad")
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
            error = "API key 验证失败，请检查项目 .env 中的 DEEPSEEK_API_KEY，并重启程序。"
        except APIConnectionError:
            error = "连接模型失败，请检查网络后重试。"
        except APIStatusError as exc:
            error = f"模型服务返回 HTTP {exc.status_code}，本轮已停止。"
        except Exception as exc:
            error = f"执行失败（{type(exc).__name__}）：{exc}"
        if error:
            close_pending_tools(messages)
            ui.notice(error, "bad")
        save_session(session, messages, ui)
        if status == "max_steps":
            ui.notice(f"已达到本轮 {MAX_STEPS} 次模型请求上限，任务可能尚未完成。可以输入新指令继续。", "warn")
        elif status == "interrupted":
            ui.notice("本轮已停止。已有文件修改不会撤销；没有返回结果的工具需要先核实执行状态。", "warn")
        elif status == "unsupported_tool":
            ui.notice("模型请求了暂不支持的工具类型，本轮已停止。", "warn")
        ui.turn_end(time.monotonic() - started)
