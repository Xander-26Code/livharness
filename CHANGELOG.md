# Changelog

[English](#unreleased) | [简体中文](#简体中文) · [Back to README](README.md)

This file records implemented changes. No formal version has been released yet, so the existing prototype and documentation updates are grouped under **Unreleased**. Future features are listed in the [roadmap](README.md#roadmap).

## Unreleased

**v0.2 milestone:** Core terminal UI and structured tool-result features are complete. A formal release has not been published.

### Added

- Streaming answers in the regular TUI and plain mode, with tool logs kept in order and no duplicate final answer. Long answers retain their full Markdown rendering in scrollback after completion.
- Partial-response notices when generation is interrupted or fails; incomplete text is not saved as a completed assistant reply.
- Tests for incremental display, tool-argument assembly, reasoning preservation, truncated tool requests, long answers, and stream cleanup. The automated suite now contains 21 tests.
- An inline Rich + prompt_toolkit terminal UI: Markdown answers, tool progress, input history, multiline input, session commands, an offline demo, and a plain mode.
- Structured tool results and explicit completion / step-limit statuses; callbacks keep display logic in `tui/`.
- UI tests for input, sessions, the step limit, and interruption. Missing tool results are recorded as unknown outcomes, not successful executions.
- An updated orbital logo based on the original sketch, plus a terminal character version.

- A session save/load test and an agent-loop test using a mocked model client. Invalid tool-call JSON must return a structured error with the correct call ID to the next model request, without executing the tool.
- Two `unittest` cases for file editing: replacing a unique match without changing surrounding text, and rejecting duplicate matches without modifying the file. Tests use temporary files and do not call a model.
- A basic model-and-tool loop using DeepSeek through the OpenAI Python SDK.
- Tools for reading, listing, finding, and editing text files, plus PDF text extraction.
- Conversation saving and loading, random session IDs, and a session list sorted by most recent update.
- English and Chinese READMEs, a contribution guide, and a dedicated changelog linked from both READMEs.

### Changed

- The agent loop now consumes DeepSeek Chat Completions streams, assembles text and tool calls, and preserves reasoning content for subsequent requests. Tool execution waits for the expected finish reason.
- Updated both READMEs and the contribution guide to reflect the completed v0.2 milestone and testing workflow.
- Standardized terminal prompts, help, and status messages in English; refreshed the README preview.
- Session lists now show conversation titles and support numbered selection from the last displayed list.

- Simplified the project goals to focus on checking task results and keeping track of current goals and constraints during long tasks.
- Updated the roadmap: v0.1 covers the basic harness; v0.2 delivers a terminal UI and structured tool results, followed by verification and context management.

Task verification and state-aware context management are **not implemented yet**. They remain the v0.3 and v0.4 goals. Reliable crash recovery is also future work; session loading currently restores saved messages.

## 简体中文

[返回中文 README](README_ZH.md)

本文件记录已经完成的改动。目前尚未正式发布版本，已有原型和文档更新统一归入「未发布」。未来计划请看[版本路线图](README_ZH.md#版本路线图)。

### 未发布

**v0.2 阶段目标：**终端界面与结构化工具结果的核心功能已完成，尚未正式发布版本。

#### 新增

- 普通 TUI 和基础模式支持流式回答，工具日志按执行顺序展示，最终回答不重复输出。长回答结束后，完整的 Markdown 排版保留在终端滚动历史中。
- 生成中断或失败时显示未完成提示；不将部分文字保存为完整的助手回答。
- 新增逐段显示、工具参数拼接、思考内容保留、工具请求截断、长回答和流式显示清理测试，自动化测试总数达到 21 项。
- 基于 Rich 和 prompt_toolkit 的连续滚动终端界面：Markdown 回答、工具进度、输入历史、多行输入、会话命令、离线预览和基础输入模式。
- 结构化工具结果、明确的完成与上限状态，通过回调将展示逻辑放在 `tui/`。
- 输入、会话、轮数上限和中断测试；缺失工具结果记为未知状态，不伪装成执行成功。
- 基于原始草图优化的圆环标志，以及终端字符版本。

- 会话保存加载测试，以及使用模拟模型客户端的主循环测试：工具参数 JSON 错误时，不执行工具，并把带有正确调用 ID 的结构化错误交给下一轮模型请求。
- 两个基于 `unittest` 的文件编辑测试：正常替换唯一匹配且保留其他内容，以及原文重复时拒绝修改并保持文件原样。使用临时文件，不调用模型。
- 通过 OpenAI Python SDK 调用 DeepSeek 的基础模型与工具循环。
- 文本读取、目录浏览、文件查找、文本编辑和 PDF 文字提取工具。
- 对话保存与加载、随机会话 ID，以及按最近更新时间排序的会话列表。
- 中英文 README、贡献指南，以及带有 README 跳转入口的独立更新日志。

#### 调整

- Agent 循环接收 DeepSeek Chat Completions 流式响应，拼接文字和工具调用，并保留后续请求所需的思考内容；确认结束原因符合预期后才执行工具。
- 同步更新中英文 README 和贡献指南，说明 v0.2 阶段完成情况与测试方法。
- 终端提示、帮助和状态信息统一使用英文，并更新 README 预览图。
- 会话列表显示对话标题，支持按最近展示的列表编号恢复会话。

- 简化项目目标，聚焦任务结果检查，以及在长任务中跟进当前目标和重要限制。
- 更新版本路线图：v0.1 完成基础 harness，v0.2 实现终端界面和结构化工具结果，之后推进结果检查与上下文管理。

任务验收和状态感知上下文管理**尚未实现**，分别保留为 v0.3 和 v0.4 的目标。可靠的崩溃恢复也是后续工作，目前加载会话恢复的是已保存的消息。
