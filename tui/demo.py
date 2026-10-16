"""离线预览：只展示界面，不调用 API，不创建会话或修改文件。"""

from agent_loop import MODEL
from tui.render import TerminalUI


def show_demo(ui: TerminalUI | None = None) -> None:
    ui = ui or TerminalUI()
    ui.welcome("preview-session", MODEL)
    ui.notice("离线界面演示 · 以下为示例内容，没有调用模型或执行工具。", "warn")
    ui.user("看看 tools 目录有哪些工具，再解释 read_file 是怎么工作的。")
    with ui.working():
        ui.event("model_start", {"step": 1, "max_steps": 10})
        ui.event("tool_start", {"tool": "list_files", "arguments": {"directory": "tools"}})
        ui.event("tool_result", {"tool": "list_files", "status": "success", "summary": "找到 5 个工具模块", "data": {}})
        ui.event("model_start", {"step": 2, "max_steps": 10})
        ui.event("tool_start", {"tool": "read_file", "arguments": {"file_path": "tools/read_file.py"}})
        ui.event("tool_result", {"tool": "read_file", "status": "success", "summary": "文件读取完成", "data": {}})
        ui.event("model_start", {"step": 3, "max_steps": 10})
        ui.response("这里有 **5 个工具**：`read_file`、`list_files`、`find_files`、`edit_file` 和 `pdf_read`。\n\n`read_file` 接收文件路径，读取文本后返回结构化结果。Agent 把这个结果交给模型，再由模型回答你。\n\n```python\nresult = read_file(file_path=\"hello.txt\")\nprint(result.status)\n```\n\n你可以用 `/details` 查看后续工具返回的完整 JSON。")
    ui.notice("演示结束。运行 python main.py 开始真实对话。", "accent")
