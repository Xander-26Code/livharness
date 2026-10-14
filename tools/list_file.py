from pathlib import Path

def list_files(directory: str) -> str:
    """
    List all files in the specified directory.

    Args:
        directory (str): The path to the directory.
    Returns:
        str: A string containing the list of files, separated by newlines.
    """
    if not isinstance(directory, str):
        return "Error: The directory path must be a string."
    path = Path(directory)
    if not path.is_dir():
        return f"Error: The path {directory} is not a valid directory."
    else:
        if not path.exists():
            return f"Error: The directory {directory} does not exist."

    name = []

    for item in path.iterdir():
        if item.is_file():
            name.append(f"[file] {item.name}")
        elif item.is_dir():
            name.append(f"[dir] {item.name}")

    return "\n".join(name) if name else f"No files found in directory {directory}."