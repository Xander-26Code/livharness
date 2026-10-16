import asyncio
import json
import os
import unittest
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from prompt_toolkit import PromptSession
from prompt_toolkit.document import Document
from prompt_toolkit.input.defaults import create_pipe_input
from prompt_toolkit.output import DummyOutput
from rich.console import Console

from tui.app import close_pending_tools, resolve_resume_id, run_app
from session import QueryEngine, get_session_title, list_sessions
from tui.demo import show_demo
from tui.input import CommandCompleter, input_bindings
from tui.render import TerminalUI


class TestTerminalUI(unittest.TestCase):
    def test_session_titles_and_unreadable_files(self):
        self.assertEqual(get_session_title([]), "New conversation")
        self.assertEqual(get_session_title([
            {"role": "system", "content": "ignore"},
            {"role": "user", "content": "  "},
            {"role": "user", "content": "解释\n  [red] 标签"},
        ]), "解释 [red] 标签")
        with TemporaryDirectory() as directory:
            QueryEngine('topic', directory).save_messages([{'role': 'user', 'content': '解释 [red] 标签'}])
            QueryEngine('empty', directory).save_messages([])
            Path(directory, 'broken_messages.json').write_text('{broken')
            Path(directory, 'invalid_messages.json').write_text('{}')
            for selectable in (True, False):
                with self.subTest(selectable=selectable):
                    output = StringIO()
                    ui = TerminalUI(console=Console(file=output, width=100, color_system=None))
                    ui.sessions(['topic', 'empty', 'broken', 'invalid', 'missing'], directory, selectable=selectable)
                    text = output.getvalue()
                    self.assertIn('解释 [red] 标签', text)
                    self.assertIn('New conversation', text)
                    self.assertEqual(text.count('Unable to read this session'), 3)
                    self.assertIn('#' if selectable else 'SESSION ID', text)

    def test_resume_number_requires_a_displayed_list_and_valid_range(self):
        for value, ids in [('1', []), ('0', ['a']), ('2', ['a'])]:
            with self.subTest(value=value, ids=ids), self.assertRaises(ValueError):
                resolve_resume_id(value, ids)
        self.assertEqual(resolve_resume_id('1', ['a', 'b']), 'a')
        self.assertEqual(resolve_resume_id('full-id', []), 'full-id')
        self.assertEqual(resolve_resume_id('1' * 32, []), '1' * 32)

    def test_resume_number_uses_displayed_order_even_after_files_change(self):
        output = StringIO()
        ui = TerminalUI(console=Console(file=output, width=100, color_system=None), plain=True)
        with TemporaryDirectory() as directory:
            for name, updated in [('first', 300), ('second', 200), ('current', 100)]:
                QueryEngine(name, directory).save_messages([
                    {'role': 'system', 'content': 'system'}, {'role': 'user', 'content': f'Topic {name}'},
                ])
                os.utime(Path(directory, f'{name}_messages.json'), (updated, updated))
            commands = iter(['/resume', '/resume 1', '/session', '/exit'])

            def read(_session_id):
                command = next(commands)
                if command == '/resume 1':
                    # 展示后另一个会话更新了；用户选择的编号仍应指向原来的第一项。
                    os.utime(Path(directory, 'second_messages.json'), (500, 500))
                return command

            with patch('tui.app.TerminalUI', return_value=ui), patch('tui.app.TerminalInput') as reader, patch('tui.app.run_agent') as agent, patch('tui.app.list_sessions', wraps=list_sessions) as listing:
                reader.return_value.read.side_effect = read
                run_app(resume_id='current', plain=True, session_dir=directory)
                listing.assert_called_once_with(directory)
                agent.assert_not_called()
            self.assertIn('Session ID: first', output.getvalue())

    def test_demo_renders_at_narrow_and_wide_widths_without_api(self):
        for width in (40, 80, 120):
            with self.subTest(width=width):
                output = StringIO()
                ui = TerminalUI(console=Console(file=output, width=width, color_system=None))
                with patch('agent_loop.get_client', side_effect=AssertionError('No API in demo')):
                    show_demo(ui)
                text = output.getvalue()
                self.assertIn('LivHarness', text)
                self.assertIn('read_file', text)
                self.assertIn('Offline', text)

    def test_input_accepts_multiline_and_bracketed_paste(self):
        async def check():
            with create_pipe_input() as pipe:
                prompt = PromptSession(input=pipe, output=DummyOutput(), multiline=True, key_bindings=input_bindings())
                pipe.send_text('first\nsecond\r')
                self.assertEqual(await prompt.prompt_async(), 'first\nsecond')
                pipe.send_text('\x1b[200~paste\nsecond line\x1b[201~\r')
                self.assertEqual(await prompt.prompt_async(), 'paste\nsecond line')
        asyncio.run(check())

    def test_completion_only_applies_to_commands(self):
        completer = CommandCompleter()
        choices = list(completer.get_completions(Document('/res'), None))
        self.assertEqual([choice.text for choice in choices], ['/resume'])
        self.assertEqual(list(completer.get_completions(Document('解释 /res'), None)), [])

    def test_interrupted_tool_batch_preserves_completed_result(self):
        messages = [
            {'role': 'assistant', 'tool_calls': [
                {'id': 'done', 'type': 'function', 'function': {'name': 'read_file', 'arguments': '{}'}},
                {'id': 'pending', 'type': 'function', 'function': {'name': 'edit_file', 'arguments': '{}'}},
            ]},
            {'role': 'tool', 'tool_call_id': 'done', 'content': 'original result'},
        ]
        close_pending_tools(messages)
        close_pending_tools(messages)
        self.assertEqual(len(messages), 3)
        self.assertEqual(messages[1]['content'], 'original result')
        self.assertEqual(messages[2]['tool_call_id'], 'pending')
        error = json.loads(messages[2]['content'])['error']
        self.assertEqual(error['code'], 'EXECUTION_INTERRUPTED')
        self.assertFalse(error['retryable'])

    def test_step_limit_saves_messages_and_accepts_another_command(self):
        output = StringIO()
        ui = TerminalUI(console=Console(file=output, color_system=None), plain=True)

        def fake_agent(messages, on_response, on_event):
            on_event('model_start', {'step': 10, 'max_steps': 10})
            messages.extend([
                {'role': 'assistant', 'tool_calls': [{'id': 'one', 'type': 'function', 'function': {'name': 'read_file', 'arguments': '{}'}}]},
                {'role': 'tool', 'tool_call_id': 'one', 'content': '{"status":"success"}'},
            ])
            return 'max_steps'

        with TemporaryDirectory() as directory, patch('tui.app.TerminalUI', return_value=ui), patch('tui.app.TerminalInput') as reader, patch('tui.app.run_agent', side_effect=fake_agent) as agent:
            reader.return_value.read.side_effect = ['test', '/session', '/exit']
            run_app(plain=True, session_dir=directory)
            saved = list(Path(directory).glob('*_messages.json'))
            self.assertEqual(len(saved), 1)
            messages = json.loads(saved[0].read_text())
            self.assertEqual(messages[-1]['role'], 'tool')
            self.assertEqual(len(messages), 4)
            agent.assert_called_once()
        self.assertIn('10-request limit', output.getvalue())
        self.assertIn('Session ID:', output.getvalue())

    def test_cancel_during_tool_call_returns_to_prompt_and_saves(self):
        ui = TerminalUI(console=Console(file=StringIO(), color_system=None), plain=True)

        def interrupt(messages, **kwargs):
            messages.append({'role': 'assistant', 'tool_calls': [
                {'id': 'interrupted', 'type': 'function', 'function': {'name': 'edit_file', 'arguments': '{}'}},
            ]})
            raise KeyboardInterrupt

        with TemporaryDirectory() as directory, patch('tui.app.TerminalUI', return_value=ui), patch('tui.app.TerminalInput') as reader, patch('tui.app.run_agent', side_effect=interrupt):
            reader.return_value.read.side_effect = ['edit', '/exit']
            run_app(plain=True, session_dir=directory)
            messages = json.loads(next(Path(directory).glob('*_messages.json')).read_text())
            self.assertEqual(messages[-1]['tool_call_id'], 'interrupted')
            self.assertEqual(json.loads(messages[-1]['content'])['error']['code'], 'EXECUTION_INTERRUPTED')

    def test_new_clear_resume_and_missing_session(self):
        ui = TerminalUI(console=Console(file=StringIO(), color_system=None), plain=True)
        from session import QueryEngine
        with TemporaryDirectory() as directory:
            old = QueryEngine('old', directory)
            old.save_messages([{'role': 'system', 'content': 'system'}, {'role': 'user', 'content': 'hello'}])
            with patch('tui.app.TerminalUI', return_value=ui), patch('tui.app.TerminalInput') as reader, patch('tui.app.run_agent') as agent:
                reader.return_value.read.side_effect = ['/new', '/resume missing', '/resume old', '/clear', '/exit']
                run_app(resume_id='old', plain=True, session_dir=directory)
                agent.assert_not_called()
            self.assertEqual(old.load_messages('old'), [{'role': 'system', 'content': 'system'}])
            self.assertEqual(len(list(Path(directory).glob('*_messages.json'))), 2)
