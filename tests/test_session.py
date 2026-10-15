import unittest
from tempfile import TemporaryDirectory

from session import QueryEngine
from openai.types.chat import ChatCompletionMessageParam

class TestSession(unittest.TestCase):
    def test_session(self):
        with TemporaryDirectory() as directory:
            messages: list[ChatCompletionMessageParam] = [
                {
                    "role": "system",
                    "content": "You are a helpful assistant that can read and list files in the local directory."
                },
                {
                    "role": "user",
                    "content": "Hello, assistant!"
                },
                {
                    "role": "assistant",
                    "content": "Hello! How can I assist you today?"
                }
            ]
            engine = QueryEngine(session_id="test_session", session_dir=directory)
            engine.save_messages(messages)
            loaded_messages = engine.load_messages("test_session")
            self.assertEqual(messages, loaded_messages)