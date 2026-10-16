"""Offline preview: no API calls, session writes, or tool execution."""

from agent_loop import MODEL
from tui.render import TerminalUI


def show_demo(ui: TerminalUI | None = None) -> None:
    ui = ui or TerminalUI()
    ui.welcome("demo0001", MODEL)
    ui.notice("Offline demo · sample conversation; no model or tools were called.", "warn")
    ui.user("Explore the tools folder and explain how read_file works.")
    with ui.working():
        ui.event("model_start", {"step": 1, "max_steps": 10})
        ui.event("tool_start", {"tool": "list_files", "arguments": {"directory": "tools"}})
        ui.event("tool_result", {"tool": "list_files", "status": "success", "summary": "Found 5 tool modules", "data": {}})
        ui.event("model_start", {"step": 2, "max_steps": 10})
        ui.event("tool_start", {"tool": "read_file", "arguments": {"file_path": "tools/read_file.py"}})
        ui.event("tool_result", {"tool": "read_file", "status": "success", "summary": "File read successfully", "data": {}})
        ui.event("model_start", {"step": 3, "max_steps": 10})
        ui.response("There are **5 tools**: `read_file`, `list_files`, `find_files`, `edit_file`, and `pdf_read`.\n\n`read_file` takes a file path and returns its contents in a structured result. The agent sends that result back to the model to answer your question.\n\n```python\nresult = read_file(file_path=\"hello.txt\")\nprint(result.status)\n```\n\nUse `/details` to inspect the full JSON from subsequent tool calls.")
    ui.notice("Demo complete. Run python main.py to start a real conversation.", "accent")
