from pathlib import Path
def find_files(directory: str, pattern: str) -> str:
    if not isinstance(directory, str):
        return "Error: The directory path must be a string."

    if not isinstance(pattern, str):
        return "Error: The pattern must be a string."

    root = Path(directory)

    if not root.is_dir():
        return f"Error: The path {directory} is not a valid directory."

    matches = []

    for path in root.rglob(pattern):
        if path.is_file():
            matches.append(f"[file] {path.relative_to(root)}")

        if len(matches) >= 100:
            break

    if not matches:
        return f"No files found in directory {directory} matching pattern '{pattern}'."

    return "\n".join(matches)