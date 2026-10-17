
from pypdf import PdfReader
from pypdf.errors import PyPdfError
from tool_result import ToolError, ToolResult

MAX_PDF_PAGES = 100
MAX_PDF_CHARACTERS = 100_000
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
        # 用 with 关闭文件；解析和提取时的异常都在同一个 try 内处理。
        with open(file_path, "rb") as file:
            reader = PdfReader(file)
            if reader.is_encrypted:
                return ToolResult(
                    tool="pdf_read", status="error", summary="Encrypted PDF is unsupported",
                    data={}, error=ToolError("ENCRYPTED_PDF", "Use an unencrypted copy of the PDF."),
                )
            if len(reader.pages) > MAX_PDF_PAGES:
                return ToolResult(
                    tool="pdf_read", status="error", summary="PDF has too many pages",
                    data={}, error=ToolError("PDF_TOO_LARGE", f"Limit: {MAX_PDF_PAGES} pages. Split the PDF first."),
                )
            content = []
            total = 0
            for page in reader.pages:
                page_text = page.extract_text() or ""
                total += len(page_text) + (1 if content else 0)
                if total > MAX_PDF_CHARACTERS:
                    return ToolResult(
                        tool="pdf_read", status="error", summary="PDF text is too large",
                        data={}, error=ToolError("PDF_TOO_LARGE", f"Limit: {MAX_PDF_CHARACTERS} characters. Split the PDF first; no partial content was returned."),
                    )
                content.append(page_text)
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

    except (PyPdfError, OSError, ValueError) as error:
        return ToolResult(
            tool="pdf_read", status="error", summary="Could not parse PDF",
            data={}, error=ToolError("PDF_READ_ERROR", str(error)),
        )

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
