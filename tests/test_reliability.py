"""回归测试：失败不能毁掉原文件，也不能留下没有结果的工具调用。"""

import json
from pathlib import Path
import stat
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import Mock, patch

from pypdf import PdfWriter

import agent_loop
from session import QueryEngine
from tools.edit_file import edit_file
from tools.pdf_read import pdf_read
from tools.read_file import read_file
from test_agent_loop import fake_stream, make_chunk


class TestPersistenceFailures(unittest.TestCase):
    def test_failed_session_replace_preserves_old_history_and_cleans_temp(self):
        with TemporaryDirectory() as directory:
            engine = QueryEngine("demo", directory)
            original = [{"role": "user", "content": "original"}]
            engine.save_messages(original)
            with patch("file_io.os.replace", side_effect=OSError("disk failure")):
                with self.assertRaises(OSError):
                    engine.save_messages([{"role": "user", "content": "new"}])
            self.assertEqual(engine.load_messages("demo"), original)
            self.assertEqual(len(list(Path(directory).iterdir())), 1)

    def test_failed_edit_preserves_original_bytes(self):
        with TemporaryDirectory() as directory:
            path = Path(directory, "demo.txt")
            original = b"hello\r\nworld\r\n"
            path.write_bytes(original)
            with patch("file_io.os.replace", side_effect=OSError("disk failure")):
                result = edit_file(str(path), "hello", "changed")
            self.assertEqual(result.status, "error")
            self.assertEqual(path.read_bytes(), original)
            self.assertEqual(len(list(Path(directory).iterdir())), 1)

    def test_edit_preserves_permissions_and_line_endings(self):
        with TemporaryDirectory() as directory:
            path = Path(directory, "demo.txt")
            path.write_bytes(b"hello\r\nworld\r\n")
            path.chmod(0o640)
            self.assertEqual(edit_file(str(path), "hello", "changed").status, "success")
            self.assertEqual(path.read_bytes(), b"changed\r\nworld\r\n")
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o640)

    def test_rejects_corrupt_history_before_restoring_it(self):
        histories = [
            {}, [{"role": "unknown", "content": "hi"}],
            [{"role": "user", "content": 42}],
            [{"role": "assistant", "tool_calls": [None]}],
            [{"role": "assistant", "tool_calls": {}}],
            [{"role": "tool", "content": "ok", "tool_call_id": "orphan"}],
            [{"role": "assistant", "tool_calls": [{"id": "x", "type": "function", "function": {}}]}],
        ]
        with TemporaryDirectory() as directory:
            engine = QueryEngine("demo", directory)
            path = Path(directory, "demo_messages.json")
            for history in histories:
                with self.subTest(history=history):
                    path.write_text(json.dumps(history), encoding="utf-8")
                    with self.assertRaises(ValueError):
                        engine.load_messages("demo")

    def test_session_id_cannot_escape_directory(self):
        with TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                QueryEngine("../outside", directory)
            with self.assertRaises(ValueError):
                QueryEngine("demo", directory).load_messages("../outside")


class TestToolFailures(unittest.TestCase):
    def test_text_limit_returns_error_not_silent_truncation(self):
        with TemporaryDirectory() as directory:
            path = Path(directory, "text.txt")
            path.write_text("12345", encoding="utf-8")
            with patch("tools.read_file.MAX_TEXT_CHARACTERS", 4):
                result = read_file(str(path))
            self.assertEqual(result.error.code, "FILE_TOO_LARGE")
            self.assertEqual(result.data, {})

    def test_invalid_and_missing_pdf_return_structured_errors(self):
        with TemporaryDirectory() as directory:
            path = Path(directory, "bad.pdf")
            self.assertEqual(pdf_read(str(path)).error.code, "FILE_NOT_FOUND")
            path.write_bytes(b"%PDF-1.7\nnot a complete PDF")
            self.assertEqual(pdf_read(str(path)).error.code, "PDF_READ_ERROR")

    def test_blank_encrypted_and_oversized_pdf(self):
        with TemporaryDirectory() as directory:
            path = Path(directory, "demo.pdf")
            writer = PdfWriter()
            writer.add_blank_page(width=100, height=100)
            writer.write(str(path))
            self.assertEqual(pdf_read(str(path)).error.code, "NO_READABLE_TEXT")
            with patch("tools.pdf_read.MAX_PDF_PAGES", 0):
                self.assertEqual(pdf_read(str(path)).error.code, "PDF_TOO_LARGE")
            writer.encrypt("test-password")
            writer.write(str(path))
            self.assertEqual(pdf_read(str(path)).error.code, "ENCRYPTED_PDF")

    def test_extracted_pdf_text_limit(self):
        with TemporaryDirectory() as directory:
            path = Path(directory, "demo.pdf")
            writer = PdfWriter()
            writer.add_blank_page(width=100, height=100)
            writer.write(str(path))
            with patch("pypdf._page.PageObject.extract_text", return_value="12345"), patch("tools.pdf_read.MAX_PDF_CHARACTERS", 4):
                result = pdf_read(str(path))
            self.assertEqual(result.error.code, "PDF_TOO_LARGE")
            self.assertEqual(result.data, {})

    def test_bad_arguments_and_tool_failures_reach_next_model_request(self):
        cases = [
            ("null", Mock(), "INVALID_TOOL_ARGUMENTS"),
            ("[]", Mock(), "INVALID_TOOL_ARGUMENTS"),
            ('{"file_path":"demo.txt"}', Mock(side_effect=PermissionError("denied")), "TOOL_EXECUTION_ERROR"),
            ('{"file_path":"demo.txt"}', Mock(return_value="wrong result type"), "INVALID_TOOL_RESULT"),
        ]
        for arguments, tool, code in cases:
            with self.subTest(code=code, arguments=arguments):
                messages = [{"role": "user", "content": "read"}]
                api = Mock()
                api.chat.completions.create.side_effect = [
                    fake_stream([
                        make_chunk({"tool_calls": [{"index": 0, "id": "call_x", "type": "function", "function": {"name": "read_file", "arguments": arguments}}]}),
                        make_chunk({}, "tool_calls"),
                    ]),
                    fake_stream([make_chunk({"content": "Could not read."}), make_chunk({}, "stop")]),
                ]
                with patch.object(agent_loop, "get_client", return_value=api), patch.dict(agent_loop.tool_functions, {"read_file": tool}):
                    status = agent_loop.run_agent(messages, on_response=Mock(), on_event=Mock())
                self.assertEqual(status, "completed")
                self.assertEqual(api.chat.completions.create.call_count, 2)
                result = json.loads(messages[2]["content"])
                self.assertEqual(result["error"]["code"], code)
                self.assertEqual(messages[2]["tool_call_id"], "call_x")
                if code == "INVALID_TOOL_ARGUMENTS":
                    tool.assert_not_called()

    def test_missing_call_id_never_executes_tool(self):
        api = Mock()
        api.chat.completions.create.return_value = fake_stream([
            make_chunk({"tool_calls": [{"index": 0, "type": "function", "function": {"name": "read_file", "arguments": "{}"}}]}),
            make_chunk({}, "tool_calls"),
        ])
        tool = Mock()
        messages = [{"role": "user", "content": "read"}]
        with patch.object(agent_loop, "get_client", return_value=api), patch.dict(agent_loop.tool_functions, {"read_file": tool}):
            with self.assertRaises(RuntimeError):
                agent_loop.run_agent(messages, on_event=Mock())
        tool.assert_not_called()
        self.assertEqual(len(messages), 1)
