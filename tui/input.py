"""可编辑的输入区：命令补全、当前会话的输入历史、多行粘贴。"""

import sys

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.styles import Style

COMMANDS = {
    "/help": "Help", "/new": "New session", "/sessions": "Saved sessions",
    "/resume": "Resume: /resume NUMBER or ID", "/session": "Current session",
    "/clear": "Clear context", "/details": "Tool result details", "/exit": "Exit",
}


class CommandCompleter(Completer):
    def get_completions(self, document, complete_event):
        prefix = document.text_before_cursor
        if prefix.startswith("/") and " " not in prefix and "\n" not in prefix:
            for command, description in COMMANDS.items():
                if command.startswith(prefix):
                    yield Completion(command, start_position=-len(prefix), display_meta=description)


def input_bindings() -> KeyBindings:
    bindings = KeyBindings()

    @bindings.add("enter")
    def submit(event):
        event.current_buffer.validate_and_handle()

    @bindings.add("c-j")
    @bindings.add("escape", "enter")
    def newline(event):
        event.current_buffer.insert_text("\n")

    return bindings


class TerminalInput:
    def __init__(self, plain: bool = False):
        self.plain = plain or not (sys.stdin.isatty() and sys.stdout.isatty())
        self.session = None
        if not self.plain:
            self.session = PromptSession(
                message=[("class:prompt", "❯ ")],
                multiline=True,
                prompt_continuation="· ",
                key_bindings=input_bindings(),
                history=InMemoryHistory(),
                completer=CommandCompleter(),
                complete_while_typing=True,
                reserve_space_for_menu=3,
                erase_when_done=True,
                style=Style.from_dict({
                    "prompt": "#56d6cf bold", "bottom-toolbar": "#8a929d noreverse",
                    "completion-menu.completion.current": "bg:#244847 #ffffff",
                }),
            )

    def set_history(self, messages: list) -> None:
        if self.session:
            history = InMemoryHistory()
            for message in messages:
                if message["role"] == "user" and isinstance(message.get("content"), str):
                    history.append_string(message["content"])
            self.session.default_buffer.history = history

    def read(self, session_id: str) -> str:
        if self.session is None:
            return input("❯ ")
        return self.session.prompt(bottom_toolbar=[("class:bottom-toolbar", f" {session_id[:8]}  ·  Enter send  ·  Ctrl+J newline  ·  /help")])
