
from pypdf import PdfReader

def pdf_read(file_path):
    """
    Reads the content of a PDF file and returns it as a string.

    Args:
        file_path (str): The path to the PDF file to be read.
    """
    if not isinstance(file_path, str):
        return "Error: The file path must be a string."
    try:
        reader = PdfReader(file_path)
    except FileNotFoundError:
        return f"Error: The file at {file_path} was not found."
    except IsADirectoryError:
        return f"Error: The path {file_path} is a directory, not a file."
    except PermissionError:
        return f"Error: Permission denied when trying to read the file at {file_path}."

    content = []

    for page in reader.pages:
        content.append(page.extract_text())

    text = "\n".join(content)

    if not text.strip():
        return f"Error: The PDF file at {file_path} contains no readable text."
    return text