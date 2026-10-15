from tool_result import ToolResult, ToolError


def read_file(file_path) -> ToolResult:
    """
    Reads the content of a file and returns it as a string.

    Args:
        file_path (str): The path to the file to be read.
    """
    if not isinstance(file_path, str):
        return ToolResult(
            tool="read_file",
            status="error",
            summary="Invalid file path",
            data={},
            error=ToolError(
                code="INVALID_FILE_PATH",
                message="The file path must be a string.",
                retryable=False
            )
        )
    try: 
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        return ToolResult(
            tool="read_file",
            status="success",
            summary="File read successfully",
            data={"content": content},
            error=None
        )
    except FileNotFoundError:
        return ToolResult(
            tool="read_file",
            status="error",
            summary="File not found",
            data={},
            error=ToolError(
                code="FILE_NOT_FOUND",
                message=f"The file at path '{file_path}' was not found.",
                retryable=False
            )
        )
    except IsADirectoryError:
        return ToolResult(
            tool="read_file",
            status="error",
            summary="Path is a directory",
            data={},
            error=ToolError(
                code="IS_A_DIRECTORY",
                message=f"The path '{file_path}' is a directory, not a file.",
                retryable=False
            )
        )
    except PermissionError:
        return ToolResult(
            tool="read_file",
            status="error",
            summary="Permission denied",
            data={},
            error=ToolError(
                code="PERMISSION_DENIED",
                message=f"Permission denied when trying to read the file at '{file_path}'.",
                retryable=False
            )
        )
    except UnicodeDecodeError:
        return ToolResult(
            tool="read_file",
            status="error",
            summary="File encoding error",
            data={},
            error=ToolError(
                code="UNICODE_DECODE_ERROR",
                message=f"The file at path '{file_path}' could not be decoded. It may not be a text file.",
                retryable=False
            )
        )