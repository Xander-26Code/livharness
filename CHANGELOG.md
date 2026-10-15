# Changelog

[English](#unreleased) | [简体中文](#简体中文) · [Back to README](README.md)

This file records implemented changes. No formal version has been released yet, so the existing prototype and documentation updates are grouped under **Unreleased**. Future features are listed in the [roadmap](README.md#roadmap).

## Unreleased

### Added

- A basic model-and-tool loop using DeepSeek through the OpenAI Python SDK.
- Tools for reading, listing, finding, and editing text files, plus PDF text extraction.
- Conversation saving and loading, random session IDs, and a session list sorted by most recent update.
- English and Chinese READMEs, a contribution guide, and a dedicated changelog linked from both READMEs.

### Changed

- Simplified the project goals to focus on checking task results and keeping track of current goals and constraints during long tasks.
- Updated the roadmap: v0.1 covers the basic harness; v0.2 plans a terminal UI and structured tool results, followed by verification and context management.

The terminal UI, structured tool results, task verification, and state-aware context management are **not implemented yet**.

## 简体中文

[返回中文 README](README_ZH.md)

本文件记录已经完成的改动。目前尚未正式发布版本，已有原型和文档更新统一归入「未发布」。未来计划请看[版本路线图](README_ZH.md#版本路线图)。

### 未发布

#### 新增

- 通过 OpenAI Python SDK 调用 DeepSeek 的基础模型与工具循环。
- 文本读取、目录浏览、文件查找、文本编辑和 PDF 文字提取工具。
- 对话保存与加载、随机会话 ID，以及按最近更新时间排序的会话列表。
- 中英文 README、贡献指南，以及带有 README 跳转入口的独立更新日志。

#### 调整

- 简化项目目标，聚焦任务结果检查，以及在长任务中跟进当前目标和重要限制。
- 更新版本路线图：v0.1 完成基础 harness，v0.2 计划增加终端界面和结构化工具结果，之后推进结果检查与上下文管理。

终端界面、结构化工具结果、任务验收和状态感知上下文管理**尚未实现**。
