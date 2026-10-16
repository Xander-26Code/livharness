# Changelog

[English](#unreleased) | [简体中文](#简体中文) · [Back to README](README.md)

This file records implemented changes. No formal version has been released yet, so the existing prototype and documentation updates are grouped under **Unreleased**. Future features are listed in the [roadmap](README.md#roadmap).

## Unreleased

### Added

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

- Standardized terminal prompts, help, and status messages in English; refreshed the README preview.
- Session lists now show conversation titles and support numbered selection from the last displayed list.

- Simplified the project goals to focus on checking task results and keeping track of current goals and constraints during long tasks.
- Updated the roadmap: v0.1 covers the basic harness; v0.2 plans a terminal UI and structured tool results, followed by verification and context management.

Task verification and state-aware context management are **not implemented yet**. The TUI is an initial implementation; token streaming and reliable crash recovery remain future work.

## 简体中文

[返回中文 README](README_ZH.md)

本文件记录已经完成的改动。目前尚未正式发布版本，已有原型和文档更新统一归入「未发布」。未来计划请看[版本路线图](README_ZH.md#版本路线图)。

### 未发布

#### 新增

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

- 终端提示、帮助和状态信息统一使用英文，并更新 README 预览图。
- 会话列表显示对话标题，支持按最近展示的列表编号恢复会话。

- 简化项目目标，聚焦任务结果检查，以及在长任务中跟进当前目标和重要限制。
- 更新版本路线图：v0.1 完成基础 harness，v0.2 计划增加终端界面和结构化工具结果，之后推进结果检查与上下文管理。

任务验收和状态感知上下文管理**尚未实现**。终端界面已有初版；逐字流式输出和可靠的崩溃恢复仍是后续工作。
