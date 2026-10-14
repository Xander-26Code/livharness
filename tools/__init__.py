from .read_file import read_file
from .list_file import list_files
from openai.types.chat import  ChatCompletionToolParam, ChatCompletionMessageParam

tool_functions = {
    "read_file": read_file,
    "list_files": list_files,
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
    }
]
