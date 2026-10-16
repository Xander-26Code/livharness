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
            Text(f"{model}  ·  {'继续会话' if resumed else '新会话'} {session_id[:8]}", style="muted"),
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
        self.console.print(Text("  输入任务开始  ·  /help 帮助  ·  /sessions 历史会话", style="muted"))
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
            self.notice("模型没有返回文字。", "warn")
        self.console.print()

    def notice(self, text: str, style: str = "muted") -> None:
        self.console.print(Text(f"  · {text}", style=style))

    @contextmanager
    def working(self):
        self.steps = 0
        self.tool_count = 0
        if self.console.is_terminal and not self.plain:
            self._status = self.console.status(Text("正在连接模型…", style="muted"), spinner="dots", spinner_style="accent")
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
            label = Text(f"模型处理中  ·  {self.steps}/{data['max_steps']} 轮  ·  Ctrl+C 停止", style="muted")
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
                self._status.update(Text(f"正在执行 {data['tool']}  ·  Ctrl+C 停止", style="muted"))
        elif name == "tool_result":
            ok = data["status"] == "success"
            summary = " ".join(str(data["summary"]).split())[:180]
            self.console.print(Text(f"    {'✓' if ok else '×'} {data['tool']} · {summary}", style="good" if ok else "bad"))
            if not ok and data.get("error"):
                self.notice(str(data["error"]["message"]), "bad")
            if self.details:
                self.console.print(Panel(
                    Syntax(json.dumps(data, ensure_ascii=False, indent=2), "json", word_wrap=True, background_color="default"),
                    title=Text("工具结果", style="muted"), border_style="border",
                ))

    def turn_end(self, elapsed: float) -> None:
        self.notice(f"{elapsed:.1f}s  ·  {self.steps} 轮模型请求  ·  {self.tool_count} 次工具调用")
        self.console.print()

    def help(self) -> None:
        rows = [
            ("/help", "查看帮助"), ("/new", "创建新会话，保留原会话"),
            ("/sessions", "查看会话列表，最近更新的在前"),
            ("/resume ID", "切换到指定会话"), ("/session", "查看当前会话 ID"),
            ("/clear", "清空当前对话上下文，不撤销文件修改"),
            ("/details", "开关后续工具结果的完整 JSON 展示"),
            ("/exit", "退出；也支持 exit、quit、Ctrl+D"),
        ]
        table = Table.grid(padding=(0, 3))
        table.add_column(style="accent")
        table.add_column()
        for command, description in rows:
            table.add_row(command, description)
        self.console.print(Panel(table, title="帮助", border_style="border"))
        self.notice("Enter 发送 · Ctrl+J 或 Esc 后 Enter 换行 · ↑/↓ 输入历史 · Tab 补全命令")
        self.notice("输入时 Ctrl+C 清空输入；执行时 Ctrl+C 停止本轮。停止不会撤销已经完成的文件修改。")

    def sessions(self, session_ids: list[str], directory: str) -> None:
        if not session_ids:
            self.notice("还没有保存的会话。")
            return
        table = Table(box=box.SIMPLE, header_style="muted", padding=(0, 1))
        table.add_column("最近更新")
        table.add_column("SESSION ID", style="accent", overflow="fold")
        for session_id in session_ids:
            path = Path(directory) / f"{session_id}_messages.json"
            timestamp = datetime.fromtimestamp(path.stat().st_mtime).strftime("%m-%d %H:%M")
            table.add_row(timestamp, session_id)
        self.console.print(table)
        self.notice("输入 /resume ID 继续其中一个会话。")

    def history(self, messages: list) -> None:
        # 展示最近几条文字；全部消息仍会传给模型。
        visible = [m for m in messages if m["role"] in ("user", "assistant") and isinstance(m.get("content"), str) and m["content"]]
        if not visible:
            return
        self.notice("最近的对话 · 已恢复完整历史")
        for message in visible[-4:]:
            if message["role"] == "user":
                self.user(message["content"])
            else:
                self.response(message["content"])
