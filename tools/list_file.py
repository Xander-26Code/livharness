from pathlib import Path
from tool_result import ToolError, ToolResult
def list_files(directory: str) -> ToolResult:
    """
    List all files in the specified directory.

    Args:
        directory (str): The path to the directory.
    Returns:
        str: A string containing the list of files, separated by newlines.
    """
    if not isinstance(directory, str):
        return ToolResult(
            tool="list_files",
            status="error",
            summary="Invalid directory path",
            data={},
            error=ToolError(
                code="INVALID_DIRECTORY_PATH",
                message="The directory path must be a string.",
                retryable=False
            )
        )
    path = Path(directory)
    if not path.is_dir():
        return ToolResult(
            tool="list_files",
            status="error",
            summary="Path is not a directory",
            data={},
            error=ToolError(
                code="NOT_A_DIRECTORY",
                message=f"The path '{directory}' is not a directory.",
                retryable=False
            )
        )
    else:
        if not path.exists():
            return ToolResult(
                tool="list_files",
                status="error",
                summary="Directory does not exist",
                data={},
                error=ToolError(
                    code="DIRECTORY_NOT_FOUND",
                    message=f"The directory '{directory}' does not exist.",
                    retryable=False
                )
            )


    name = []

    for item in path.iterdir():
        if item.is_file():
            name.append(f"[file] {item.name}")
        elif item.is_dir():
            name.append(f"[dir] {item.name}")

    return ToolResult(
        tool="list_files",
        status="success",
        summary="Files listed successfully",
        data={"files": name},
        error=None
    )