from pathlib import Path
from tool_result import ToolError, ToolResult
def find_files(directory: str, pattern: str) -> ToolResult:
    if not isinstance(directory, str):
        return ToolResult(
            tool="find_files",
            status="error",
            summary="Invalid directory path",
            data={},
            error=ToolError(
                code="INVALID_DIRECTORY_PATH",
                message="The directory path must be a string.",
                retryable=False
            )
        )

    if not isinstance(pattern, str):
        return ToolResult(
            tool="find_files",
            status="error",
            summary="Invalid pattern",
            data={},
            error=ToolError(
                code="INVALID_PATTERN",
                message="The pattern must be a string.",
                retryable=False
            )
        )

    root = Path(directory)

    if not root.is_dir():
        return ToolResult(
            tool="find_files",
            status="error",
            summary="Path is not a directory",
            data={},
            error=ToolError(
                code="NOT_A_DIRECTORY",
                message=f"The path '{directory}' is not a directory.",
                retryable=False
            )
        )

    matches = []

    for path in root.rglob(pattern):
        if path.is_file():
            matches.append(f"[file] {path.relative_to(root)}")

        if len(matches) >= 100:
            break

    if not matches:
        return ToolResult(
            tool="find_files",
            status="error",
            summary="No files found",
            data={},
            error=ToolError(
                code="NO_FILES_FOUND",
                message=f"No files found in directory {directory} matching pattern '{pattern}'.",
                retryable=False
            )
        )

    return ToolResult(
        tool="find_files",
        status="success",
        summary="Files found successfully",
        data={"files": matches},
        error=None
    )