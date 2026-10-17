"""命令行入口。终端交互放在 tui/，Agent 循环仍在 agent_loop.py。"""

import argparse

from session import list_sessions
from tui.app import run_app
from tui.demo import show_demo
from tui.render import TerminalUI


def main(resume_id: str | None = None, plain: bool = False) -> None:
    run_app(resume_id=resume_id, plain=plain)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="LivHarness — a basic agent harness for learning.")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--resume", metavar="SESSION_ID", help="Continue a saved conversation")
    mode.add_argument("--list-sessions", action="store_true", help="List sessions, most recently updated first")
    mode.add_argument("--demo", action="store_true", help="Preview the terminal UI offline; no API calls")
    parser.add_argument("--plain", action="store_true", help="Use basic input without colors or animations")
    args = parser.parse_args()
    if args.demo:
        show_demo(TerminalUI(plain=args.plain))
    elif args.list_sessions:
        ui = TerminalUI(plain=args.plain)
        try:
            ui.sessions(list_sessions("sessions"), "sessions")
        except OSError as exc:
            ui.notice(f"Could not read sessions: {exc}", "bad")
    else:
        main(resume_id=args.resume, plain=args.plain)
