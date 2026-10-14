from .read_file import read_file
from .list_file import list_files
from .find_files import find_files
from .edit_file import edit_file
from .pdf_read import pdf_read
from openai.types.chat import  ChatCompletionToolParam, ChatCompletionMessageParam

tool_functions = {
    "read_file": read_file,
    "list_files": list_files,
    "find_files": find_files,
    "edit_file": edit_file,
    "pdf_read": pdf_read,
}


tools: list[ChatCompletionToolParam] = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "读取本地文本文件的内容。",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "要读取的文件路径，例如 hello.txt"
                    }
                },
                "required": ["file_path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "列出指定目录下的所有文件。",
            "parameters": {
                "type": "object",
                "properties": {
                    "directory": {
                        "type": "string",
                        "description": "要列出文件的目录路径，例如 ./"
                    }
                },
                "required": ["directory"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "find_files",
            "description": "在指定目录下查找符合模式的文件。",
            "parameters": {
                "type": "object",
                "properties": {
                    "directory": {
                        "type": "string",
                        "description": "要查找文件的目录路径，例如 ./"
                    },
                    "pattern": {
                        "type": "string",
                        "description": "要匹配的文件模式，例如 *.txt"
                    }
                },
                "required": ["directory", "pattern"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "edit_file",
            "description": "编辑本地文本文件的内容。",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "要编辑的文件路径，例如 hello.txt"
                    },
                    "old_text": {
                        "type": "string",
                        "description": "要替换的旧文本"
                    },
                    "new_text": {
                        "type": "string",
                        "description": "要替换为的新文本"
                    }
                },
                "required": ["file_path", "old_text", "new_text"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "pdf_read",
            "description": "读取本地 PDF 文件的所有页面，提取文字并返回合并后的文本。不支持扫描图片的 OCR 或图片内容理解，不保证保留表格的行列结构。",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "要读取的本地 PDF 文件路径，例如 documents/report.pdf；相对路径以程序运行时的当前工作目录为基准。"
                    }
                },
                "required": ["file_path"]
            }
        }
    }
]
