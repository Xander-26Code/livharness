
from pypdf import PdfReader
from tool_result import ToolError, ToolResult
def pdf_read(file_path) -> ToolResult:
    """
    Reads the content of a PDF file and returns it as a string.

    Args:
        file_path (str): The path to the PDF file to be read.
    """
    if not isinstance(file_path, str):
        return ToolResult(
            tool="pdf_read",
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
        reader = PdfReader(file_path)
    except FileNotFoundError:
        return ToolResult(
            tool="pdf_read",
            status="error",
            summary="File not found",
            data={},
            error=ToolError(
                code="FILE_NOT_FOUND",
                message=f"The file at {file_path} was not found.",
                retryable=False
            )
        )
    except IsADirectoryError:
        return ToolResult(
            tool="pdf_read",
            status="error",
            summary="Path is a directory",
            data={},
            error=ToolError(
                code="IS_A_DIRECTORY",
                message=f"The path {file_path} is a directory, not a file.",
                retryable=False
            )
        )
    except PermissionError:
        return ToolResult(
            tool="pdf_read",
            status="error",
            summary="Permission denied",
            data={},
            error=ToolError(
                code="PERMISSION_DENIED",
                message=f"Permission denied when trying to read the file at {file_path}.",
                retryable=False
            )
        )

    content = []

    for page in reader.pages:
        content.append(page.extract_text())

    text = "\n".join(content)

    if not text.strip():
        return ToolResult(
            tool="pdf_read",
            status="error",
            summary="No readable text",
            data={},
            error=ToolError(
                code="NO_READABLE_TEXT",
                message=f"The PDF file at {file_path} contains no readable text.",
                retryable=False
            )
        )
    return ToolResult(
        tool="pdf_read",
        status="success",
        summary="PDF content read successfully",
        data={"text": text},
        error=None
    )