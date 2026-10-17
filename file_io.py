"""先写临时文件，再替换目标，避免写到一半破坏原文件。"""

import os
from pathlib import Path
import stat
from tempfile import NamedTemporaryFile


def atomic_write_text(path: Path, content: str) -> None:
    path = path.resolve()
    mode = stat.S_IMODE(path.stat().st_mode) if path.exists() else None
    temporary = None
    try:
        with NamedTemporaryFile(
            mode="w", encoding="utf-8", newline="", dir=path.parent,
            prefix=f".{path.name}.", suffix=".tmp", delete=False,
        ) as file:
            temporary = Path(file.name)
            file.write(content)
            file.flush()
            os.fsync(file.fileno())
        if mode is not None:
            temporary.chmod(mode)
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
