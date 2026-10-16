"""Render the README preview from the real UI components, without calling an API."""

import sys
from io import StringIO
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from rich.console import Console
from rich.terminal_theme import TerminalTheme
from tui.demo import show_demo
from tui.render import TerminalUI


def main() -> None:
    console = Console(file=StringIO(), width=92, record=True, force_terminal=False)
    show_demo(TerminalUI(console=console))
    destination = ROOT / "asset" / "tui-preview.svg"
    console.save_svg(
        str(destination),
        title="LivHarness · offline preview",
        theme=TerminalTheme(
            (19, 24, 29), (222, 228, 231),
            [(19, 24, 29), (242, 154, 150), (148, 207, 162), (233, 189, 120),
             (132, 168, 218), (189, 160, 215), (86, 214, 207), (222, 228, 231)],
        ),
    )
    print(f"Saved {destination}")


if __name__ == "__main__":
    main()
