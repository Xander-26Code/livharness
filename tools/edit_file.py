from pathlib import Path


def edit_file(file_path: str, old_text: str, new_text: str) -> str:
    if not isinstance(file_path, str):
        return "Error: file_path 必须是字符串。"

    if not isinstance(old_text, str) or not isinstance(new_text, str):
        return "Error: old_text 和 new_text 必须是字符串。"

    if not old_text:
        return "Error: old_text 不能为空。"

    path = Path(file_path)

    try:
        with open(path, "r", encoding="utf-8", newline="") as file:
            content = file.read()

        count = content.count(old_text)

        if count == 0:
            return "Error: 没有找到要替换的原文，请先重新读取文件。"

        if count > 1:
            return "Error: 原文出现多次，请提供更长的原文以确定修改位置。"

        updated_content = content.replace(old_text, new_text, 1)

        with open(path, "w", encoding="utf-8", newline="") as file:
            file.write(updated_content)

        return f"已修改文件：{file_path}"

    except (OSError, UnicodeError) as error:
        return f"Error: 无法编辑文件：{error}"