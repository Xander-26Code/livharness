import json
import os
import runpy
import unittest
from contextlib import redirect_stdout
from copy import deepcopy
from io import StringIO
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from openai.types.chat import ChatCompletionMessage, ChatCompletionMessageParam
from tool_result import ToolResult


class TestAgentLoop(unittest.TestCase):
    def test_callback_and_messages_at_step_limit(self):
        # 分别验证：工具后正常回答、第10轮回答、10轮都调用工具。
        for tool_rounds, final_text in [(1, "读取完成"), (9, "读取完成"), (10, None)]:
            with self.subTest(tool_rounds=tool_rounds):
                replies = []
                for index in range(tool_rounds):
                    replies.append(ChatCompletionMessage.model_validate({
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [{
                            "id": f"call_{index}",
                            "type": "function",
                            "function": {"name": "read_file", "arguments": '{"file_path":"demo.txt"}'},
                        }],
                    }))
                if final_text is not None:
                    replies.append(ChatCompletionMessage(role="assistant", content=final_text))

                messages = [{"role": "user", "content": "读取文件"}]
                on_response = Mock()
                events = []
                read_file = Mock(return_value=ToolResult(
                    tool="read_file", status="success", summary="读取成功", data={"content": "hello"},
                ))
                agent_path = Path(__file__).resolve().parents[1] / "agent_loop.py"
                with (
                    patch("dotenv.load_dotenv"),
                    patch.dict(os.environ, {"DEEPSEEK_API_KEY": "test-only-key"}),
                    patch("openai.OpenAI") as client_class,
                    redirect_stdout(StringIO()),
                ):
                    create = client_class.return_value.chat.completions.create
                    create.side_effect = [
                        SimpleNamespace(choices=[SimpleNamespace(message=reply)]) for reply in replies
                    ]
                    agent = runpy.run_path(str(agent_path))
                    with patch.dict(agent["tool_functions"], {"read_file": read_file}):
                        status = agent["run_agent"](
                            messages,
                            on_response=on_response,
                            on_event=lambda name, data: events.append((name, data)),
                        )

                self.assertEqual(create.call_count, len(replies))
                self.assertEqual(read_file.call_count, tool_rounds)
                self.assertEqual(sum(name == "model_start" for name, _ in events), len(replies))
                self.assertEqual(sum(name == "tool_start" for name, _ in events), tool_rounds)
                self.assertEqual(sum(name == "tool_result" for name, _ in events), tool_rounds)
                self.assertEqual(events[0], ("model_start", {"step": 1, "max_steps": 10}))
                tool_messages = [item for item in messages if item["role"] == "tool"]
                self.assertEqual(len(tool_messages), tool_rounds)
                for index, item in enumerate(tool_messages):
                    self.assertEqual(item["tool_call_id"], f"call_{index}")
                    self.assertEqual(json.loads(item["content"])["data"], {"content": "hello"})
                if final_text is None:
                    self.assertEqual(status, "max_steps")
                    self.assertEqual(len(messages), 21)
                    self.assertEqual(messages[-1]["role"], "tool")
                    on_response.assert_not_called()
                else:
                    self.assertEqual(status, "completed")
                    self.assertEqual(messages[-1], {"role": "assistant", "content": final_text})
                    on_response.assert_called_once_with(final_text)

    def test_invalid_json_returns_error_without_running_tool(self):
        # 1. 模拟第一轮：模型请求读取文件，但参数缺少 JSON 值。
        tool_request = ChatCompletionMessage.model_validate({
            "role": "assistant",
            "content": None,
            "tool_calls": [{
                "id": "call_invalid_json",
                "type": "function",
                "function": {
                    "name": "read_file",
                    "arguments": '{"file_path":}',
                },
            }],
        })
        final_answer = ChatCompletionMessage(
            role="assistant",
            content="参数格式错误，需要修正。",
        )
        responses = iter([
            SimpleNamespace(choices=[SimpleNamespace(message=tool_request)]),
            SimpleNamespace(choices=[SimpleNamespace(message=final_answer)]),
        ])
        requests = []

        def fake_create(**kwargs):
            # 主循环会继续修改 messages，所以保存每次请求时的独立副本。
            requests.append(deepcopy(kwargs["messages"]))
            return next(responses)

        messages: list[ChatCompletionMessageParam] = [
            {"role": "user", "content": "请读取 demo.txt。"},
        ]
        read_file_mock = Mock()
        agent_path = Path(__file__).resolve().parents[1] / "agent_loop.py"

        # 2. 不读取真实 .env，不创建真实客户端，也不读取任何用户文件。
        with (
            patch("dotenv.load_dotenv"),
            patch.dict(os.environ, {"DEEPSEEK_API_KEY": "test-only-key"}),
            patch("openai.OpenAI") as client_class,
        ):
            client_class.return_value.chat.completions.create.side_effect = fake_create
            # 单独加载主循环，避免测试依赖其他地方是否已经导入过它。
            agent = runpy.run_path(str(agent_path))
            with (
                patch.dict(agent["tool_functions"], {"read_file": read_file_mock}),
                redirect_stdout(StringIO()),
            ):
                agent["run_agent"](messages)

        # 3. 错误参数不能触发工具；错误结果应进入下一轮模型请求。
        read_file_mock.assert_not_called()
        self.assertEqual(len(requests), 2)
        tool_messages = [item for item in requests[1] if item["role"] == "tool"]
        self.assertEqual(len(tool_messages), 1)
        self.assertEqual(tool_messages[0]["tool_call_id"], "call_invalid_json")

        result = json.loads(tool_messages[0]["content"])
        self.assertEqual(result["tool"], "read_file")
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["error"]["code"], "INVALID_JSON_ARGUMENTS")
        self.assertFalse(result["error"]["retryable"])
        self.assertEqual(messages[-1], {
            "role": "assistant",
            "content": "参数格式错误，需要修正。",
        })
