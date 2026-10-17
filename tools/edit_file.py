from pathlib import Path
from tool_result import ToolError, ToolResult
from file_io import atomic_write_text

def edit_file(file_path: str, old_text: str, new_text: str) -> ToolResult:
    if not isinstance(file_path, str):
        return ToolResult(
            tool="edit_file",
            status="error",
            summary="Invalid file path",
            data={},
            error=ToolError(
                code="INVALID_FILE_PATH",
                message="The file path must be a string.",
                retryable=False
            )
        )
    if not isinstance(old_text, str) or not isinstance(new_text, str):
        return ToolResult(
            tool="edit_file",
            status="error",
            summary="Invalid text",
            data={},
            error=ToolError(
                code="INVALID_TEXT",
                message="The old_text and new_text must be strings.",
                retryable=False
            )
        )

    if not old_text:
        return ToolResult(
            tool="edit_file",
            status="error",
            summary="Empty old text",
            data={},
            error=ToolError(
                code="EMPTY_OLD_TEXT",
                message="The old_text cannot be empty.",
                retryable=False
            )
        )

    path = Path(file_path)

    try:
        with open(path, "r", encoding="utf-8", newline="") as file:
            content = file.read()

        count = content.count(old_text)

        if count == 0:
            return ToolResult(
                tool="edit_file",
                status="error",
                summary="Text not found",
                data={},
                error=ToolError(
                    code="TEXT_NOT_FOUND",
                    message="The text to be replaced was not found in the file.",
                    retryable=False
                )
            )

        if count > 1:
            return ToolResult(
                tool="edit_file",
                status="error",
                summary="Text appears multiple times",
                data={},
                error=ToolError(
                    code="TEXT_MULTIPLE_TIMES",
                    message="The text to be replaced appears multiple times in the file. Please provide more context to specify which instance to replace.",
                    retryable=False
                )
            )

        updated_content = content.replace(old_text, new_text, 1)

        atomic_write_text(path, updated_content)

        return ToolResult(
            tool="edit_file",
            status="success",
            summary="File edited successfully",
            data={"file_path": file_path},
            error=None
        )

    except (OSError, UnicodeError) as error:
        return ToolResult(
            tool="edit_file",
            status="error",
            summary="File operation error",
            data={},
            error=ToolError(
                code="FILE_OPERATION_ERROR",
                message=f"An error occurred while accessing the file: {str(error)}",
                retryable=False
            )
        )
