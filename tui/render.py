"""Rich 只负责显示；不调用模型、不修改会话。"""

import json
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

from rich import box
from rich.console import Console, Group
from rich.markdown import Markdown
from rich.padding import Padding
from rich.panel import Panel
from rich.status import Status
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text
from rich.theme import Theme
from session import QueryEngine, get_session_title

THEME = Theme({
    "accent": "#56d6cf", "spark": "#f2a18b", "muted": "#8a929d",
    "border": "#48535e", "good": "#94cfa2", "warn": "#e9bd78", "bad": "#f29a96",
})


class TerminalUI:
    def __init__(self, console: Console | None = None, plain: bool = False):
        self.console = console or Console(theme=THEME, color_system=None if plain else "auto")
        self.console.push_theme(THEME)
        self.plain = plain
        self.details = False
        self.steps = 0
        self.tool_count = 0
        self._status: Status | None = None

    def welcome(self, session_id: str, model: str, resumed: bool = False) -> None:
        logo = Text("  ▝▚           \n", style="spark")
        logo.append("    ▄████▄     \n   ██    ██    \n   ██ ▄  ██    \n    ▀████▀     ", style="accent")
        title = Text("LivHarness", style="bold accent")
        title.append("  /  early development", style="muted")
        copy = Group(
            title,
            Text("Local tools. Clear steps.", style="muted"),
            Text(f"{model}  ·  {'resumed' if resumed else 'new session'} {session_id[:8]}", style="muted"),
            Text(str(Path.cwd()), style="muted", overflow="fold"),
        )
        layout = Table.grid(padding=(0, 1))
        if self.console.width >= 66:
            layout.add_column(width=16)
            layout.add_column(ratio=1)
            layout.add_row(logo, copy)
        else:
            layout.add_row(copy)
        self.console.print()
        self.console.print(Panel(layout, box=box.ROUNDED, border_style="border", padding=(1, 1)))
        self.console.print(Text("  Describe a task to begin  ·  /help  ·  /sessions", style="muted"))
        self.console.print()

    def user(self, text: str) -> None:
        self.console.rule(Text("YOU", style="bold spark"), align="left", style="border")
        self.console.print(Padding(Text(text), (0, 2)))
        self.console.print()

    def response(self, text: str) -> None:
        if self._status:
            self._status.stop()
        self.console.print(Text("● Liv", style="bold accent"))
        if text:
            body = Text(text) if self.plain else Markdown(text, code_theme="monokai")
            self.console.print(Padding(body, (0, 2)))
        else:
            self.notice("The model returned no text.", "warn")
        self.console.print()

    def notice(self, text: str, style: str = "muted") -> None:
        self.console.print(Text(f"  · {text}", style=style))

    @contextmanager
    def working(self):
        self.steps = 0
        self.tool_count = 0
        if self.console.is_terminal and not self.plain:
            self._status = self.console.status(Text("Connecting to the model…", style="muted"), spinner="dots", spinner_style="accent")
            self._status.start()
        try:
            yield
        finally:
            if self._status:
                self._status.stop()
                self._status = None

    def event(self, name: str, data: dict) -> None:
        if name == "model_start":
            self.steps = data["step"]
            label = Text(f"Working  ·  step {self.steps}/{data['max_steps']}  ·  Ctrl+C to stop", style="muted")
            if self._status:
                self._status.update(label)
        elif name == "tool_start":
            self.tool_count += 1
            arguments = json.dumps(data["arguments"], ensure_ascii=False)
            if len(arguments) > 110:
                arguments = arguments[:107] + "…"
            row = Text(f"  ↳ {data['tool']}  ", style="accent")
            row.append(arguments, style="muted")
            self.console.print(row)
            if self._status:
                self._status.update(Text(f"Running {data['tool']}  ·  Ctrl+C to stop", style="muted"))
        elif name == "tool_result":
            ok = data["status"] == "success"
            summary = " ".join(str(data["summary"]).split())[:180]
            self.console.print(Text(f"    {'✓' if ok else '×'} {data['tool']} · {summary}", style="good" if ok else "bad"))
            if not ok and data.get("error"):
                self.notice(str(data["error"]["message"]), "bad")
            if self.details:
                self.console.print(Panel(
                    Syntax(json.dumps(data, ensure_ascii=False, indent=2), "json", word_wrap=True, background_color="default"),
                    title=Text("Tool result", style="muted"), border_style="border",
                ))

    def turn_end(self, elapsed: float) -> None:
        self.notice(f"{elapsed:.1f}s  ·  {self.steps} model requests  ·  {self.tool_count} tool calls")
        self.console.print()

    def help(self) -> None:
        rows = [
            ("/help", "Show help"), ("/new", "Start a new session; keep the previous one"),
            ("/sessions", "List sessions, most recently updated first"),
            ("/resume NUMBER|ID", "Resume a session; omit the argument to list sessions"), ("/session", "Show the full current session ID"),
            ("/clear", "Clear conversation context; keep file changes"),
            ("/details", "Toggle full JSON for subsequent tool results"),
            ("/exit", "Save and exit; also exit, quit, or Ctrl+D"),
        ]
        table = Table.grid(padding=(0, 3))
        table.add_column(style="accent")
        table.add_column()
        for command, description in rows:
            table.add_row(command, description)
        self.console.print(Panel(table, title="Help", border_style="border"))
        self.notice("Enter send · Ctrl+J or Esc then Enter newline · ↑/↓ history · Tab complete")
        self.notice("Ctrl+C cancels input or stops the current turn. Completed file changes are not undone.")

    def sessions(self, session_ids: list[str], directory: str, selectable: bool = False) -> None:
        if not session_ids:
            self.notice("No saved sessions yet.")
            return
        table = Table(box=box.SIMPLE, header_style="muted", padding=(0, 1))
        if selectable:
            table.add_column("#", style="accent", no_wrap=True)
        table.add_column("UPDATED", no_wrap=True)
        table.add_column("CONVERSATION", style="accent", overflow="fold")
        if not selectable:
            table.add_column("SESSION ID", style="muted", overflow="fold")
        for index, session_id in enumerate(session_ids, start=1):
            path = Path(directory) / f"{session_id}_messages.json"
            timestamp = "—"
            try:
                timestamp = datetime.fromtimestamp(path.stat().st_mtime).strftime("%m-%d %H:%M")
                messages = QueryEngine(session_id, directory).load_messages(session_id)
                if not isinstance(messages, list) or not all(isinstance(m, dict) and "role" in m for m in messages):
                    raise ValueError("Invalid session message format")
                title = get_session_title(messages)
            except (OSError, ValueError):
                title = "Unable to read this session"
            # 用户的标题按普通文字显示，避免 [red] 等内容被当作 Rich 标记。
            if selectable:
                table.add_row(str(index), timestamp, Text(title))
            else:
                table.add_row(timestamp, Text(title), session_id)
        self.console.print(table)
        if selectable:
            self.notice("Use /resume 1 to continue the first session, or /resume FULL_ID.")
            self.notice("Numbers refer to this list. Use /sessions to refresh.")
        else:
            self.notice("Run python main.py --resume FULL_ID to continue a session.")

    def history(self, messages: list) -> None:
        # 展示最近几条文字；全部消息仍会传给模型。
        visible = [m for m in messages if m["role"] in ("user", "assistant") and isinstance(m.get("content"), str) and m["content"]]
        if not visible:
            return
        self.notice("Recent conversation · full history restored")
        for message in visible[-4:]:
            if message["role"] == "user":
                self.user(message["content"])
            else:
                self.response(message["content"])
