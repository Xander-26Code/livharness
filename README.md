<img src="asset/logo-v2.png" alt="LivHarness logo" width="112">

# LivHarness

[English](README.md) | [简体中文](README_ZH.md)

**A basic Python agent harness framework for beginners learning how agents work.**

LivHarness connects a language model to local tools, runs the tool-calling loop, and saves conversations. It is a small learning project you can read, run, and change—not a mature harness or a production-ready coding agent.

The project is wrapping up its initial development as a learning edition. The earlier v0.3/v0.4 product roadmap is paused. Task verification, reliable task recovery, and advanced context management have not been implemented. Small fixes, clearer explanations, and learning examples are welcome; there is no commitment to further feature releases.

## Quick start

You need Python 3.10+, Git, and a DeepSeek API key for live conversations. Offline previews and automated tests do not need a key. Development checks have been run on Python 3.13; other supported Python versions are not covered by a CI matrix.

```bash
git clone https://github.com/Xander-26Code/livharness.git
cd livharness
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
```

On Windows PowerShell, activate with `.venv\Scripts\Activate.ps1` and use `Copy-Item .env.example .env`.

Edit `.env` and replace the placeholder with your own key:

```dotenv
DEEPSEEK_API_KEY=your_deepseek_api_key
```

An existing environment variable takes precedence over `.env`. Never commit your key. The current model is `deepseek-flash`, configured alongside the API URL in [agent_loop.py](agent_loop.py). If your account does not support that model, change `MODEL` to a compatible DeepSeek model available to your account.

Run from the repository root:

```bash
python main.py --demo   # Offline UI preview; no API request or session write
python main.py          # Interactive chat; uses your API account
```

Try: **“List the files in tools/, then read tools/read_file.py and explain it.”**

If the rich interface does not display correctly, use `python main.py --plain`. Thinking mode is enabled, so the model may take some time before its answer starts streaming. Reasoning text is not displayed in the UI.

## What you can learn

The basic flow is:

```text
User input → model response → tool call request
                            → Python executes the tool
                            → tool result goes back to the model
                            → another tool request or a text answer
```

The model requests a tool; Python actually runs it. A final model answer ends the turn but does not prove that the user's task was completed correctly.

Read the code in this order:

| File | What it teaches |
| --- | --- |
| [tools/read_file.py](tools/read_file.py) | A tool's inputs, result, and errors |
| [tool_result.py](tool_result.py) | A shared result structure |
| [tools/__init__.py](tools/__init__.py) | Tool descriptions and the mapping to Python functions |
| [agent_loop.py](agent_loop.py) | Streaming, assembling tool arguments, execution, and follow-up requests |
| [session.py](session.py) | Saving and loading conversation history |
| [main.py](main.py), [tui/app.py](tui/app.py) | Connecting user input, the loop, and the terminal UI |
| [tests/](tests/) | Testing with temporary files and simulated model responses |

The interface lives in `tui/`. You can study the tools and loop before reading the display code. [file_io.py](file_io.py) contains the temporary-file replacement helper used by editing and session saving.

## Usage

- Five tools: `read_file`, `list_files`, `find_files`, `edit_file`, and `pdf_read`.
- Streaming answers, Markdown rendering, tool status, and editable terminal input.
- Structured tool errors, a ten-model-request limit per turn, and Ctrl+C interruption.
- Saved conversations with titles, update-time ordering, and numbered selection.

![Offline terminal preview](asset/tui-preview.svg)

| Command | Purpose |
| --- | --- |
| `python main.py --help` | Show CLI options |
| `python main.py --list-sessions` | List saved conversations |
| `python main.py --resume SESSION_ID` | Load a conversation by its full ID |
| `/help` | Show interactive commands |
| `/sessions`, `/resume` | Show conversations with numbers and titles |
| `/resume 1` | Load entry 1 from the last displayed list |
| `/new` | Start a new conversation |
| `/session` | Show the current ID |
| `/details` | Toggle full tool-result details |
| `/clear` | Clear conversation context; file changes remain |
| `/exit` | Save and exit |

Enter sends; Ctrl+J (or Esc then Enter) inserts a newline. Arrow keys browse input history; Tab completes commands. Ctrl+C cancels input or stops the current turn. It does not undo file changes.

## Limitations

Use disposable examples or copies of files while learning.

- **No sandbox, permission approval, or automatic rollback.** Tools use the process's filesystem permissions. Do not point the agent at secrets or important files. File contents may be sent to the model service.
- **Small-file tools.** Text reading accepts at most 100,000 characters. PDF reading accepts unencrypted PDFs of at most 100 pages and 100,000 extracted characters, with no OCR or image understanding. Over-limit reads return an error, not a silently truncated success. These limits do not guarantee bounded PDF parsing memory.
- **Limited context management.** The full conversation is sent on subsequent requests. Long conversations can exceed model limits; use `/new` to start fresh. There is no demonstrated token-saving advantage.
- **Conversation persistence, not durable task execution.** Temporary-file replacement reduces partial-write damage, but does not provide multi-process coordination, rollback, or guaranteed recovery after a crash or power loss. An interrupted tool's outcome may be unknown.
- **No independent task verification.** Tool success and model completion are not proof of task success. There is no shell execution tool or built-in project test runner.
- **One provider setup.** This example uses DeepSeek through the OpenAI Python SDK. Model availability, API access, and billing depend on your account.

## Testing

```bash
python -m unittest discover -s tests -v
```

Tests use temporary files and mocked model streams, without reading your key or making model API calls. They cover streaming, tool errors, session loading, interrupted writes, file editing, PDF failures, and terminal interaction. Passing tests do not establish production readiness or performance against other harnesses.

For a live check, start the app, read a small test file, request a missing file, exit, and resume that session. Check the actual files after any edit. Live checks consume API credits.

## Contributing and project status

This repository is now a learning reference. Please keep changes small and explain why they help beginners or fix a reproducible problem. See the [contribution guide](CONTRIBUTING.md).

**[Read the changelog →](CHANGELOG.md)**

The v0.1/v0.2 labels describe development milestones, not published releases. The previous verification and context-management roadmap is paused.

## License

Licensed under the [MIT License](LICENSE). You may use, modify, and distribute this project, including commercially, provided you retain the copyright and license notices. Third-party dependencies remain subject to their own licenses.
