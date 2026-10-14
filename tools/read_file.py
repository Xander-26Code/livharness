def read_file(file_path):
    """
    Reads the content of a file and returns it as a string.

    Args:
        file_path (str): The path to the file to be read.
    """
    if not isinstance(file_path, str):
        return "Error: The file path must be a string."
    try: 
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        return content
    except FileNotFoundError:
        return f"Error: The file at {file_path} was not found."
    except IsADirectoryError:
        return f"Error: The path {file_path} is a directory, not a file."
    except PermissionError:
        return f"Error: Permission denied when trying to read the file at {file_path}."
    except UnicodeDecodeError:
        return f"Error: The file at {file_path} could not be decoded. It may not be a text file."

