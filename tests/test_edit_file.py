import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from tools.edit_file import edit_file


class TestEditFile(unittest.TestCase):
    def test_replace_unique_text(self):
        # 1. 准备：创建临时文件，不碰真实文件。
        with TemporaryDirectory() as directory:
            path = Path(directory) / "demo.txt"
            path.write_text(
                "第一行保持不变\nHello, Xander\n最后一行保持不变\n",
                encoding="utf-8",
            )

            # 2. 执行：调用我们要测试的函数。
            result = edit_file(str(path), "Hello, Xander", "你好，xander。")

            # 3. 检查：重新读取文件，确认替换正确且没有改动其他内容。
            self.assertEqual(
                path.read_text(encoding="utf-8"),
                "第一行保持不变\n你好，xander。\n最后一行保持不变\n",
            )
            self.assertEqual(result.status, "success")
            self.assertIsNone(result.error)

    def test_reject_duplicate_text(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "demo.txt"
            original = "Hello, Xander\nHello, Xander\n"
            path.write_text(original, encoding="utf-8")
            original_bytes = path.read_bytes()

            result = edit_file(str(path), "Hello, Xander", "你好，xander。")

            # 原文出现两次时，应报错，并保留文件原样。
            self.assertEqual(result.status, "error")
            if result.error is None:
                self.fail("拒绝重复匹配时，应返回具体错误信息。")
            self.assertEqual(result.error.code, "TEXT_MULTIPLE_TIMES")
            self.assertEqual(path.read_bytes(), original_bytes)
