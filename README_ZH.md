<img src="asset/logo-v2.png" alt="LivHarness 标志" width="112">

# LivHarness

[English](README.md) | [简体中文](README_ZH.md)

**一个供初学者学习 Agent 工作原理的 Python Harness 基础框架。**

LivHarness 把大模型和本地工具连接起来，运行工具调用循环，并保存对话。你可以阅读、运行和修改它，学习一个简单 Agent 是怎么搭起来的。它不是成熟的 Harness，也不是可用于生产的编程助手。

项目以基础学习版的定位完成这一阶段的收尾，暂停原来的 v0.3/v0.4 产品路线。任务验收、可靠的任务恢复和高级上下文管理均未实现。欢迎小型修复、易懂的解释和学习示例，不承诺继续发布新功能。

## 快速开始

需要 Python 3.10+、Git，以及用于真实对话的 DeepSeek API Key。离线预览和自动化测试不需要密钥。目前开发检查使用 Python 3.13，尚未通过 CI 矩阵验证其他支持版本。

```bash
git clone https://github.com/Xander-26Code/livharness.git
cd livharness
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
```

Windows PowerShell 使用 `.venv\Scripts\Activate.ps1` 激活环境，使用 `Copy-Item .env.example .env` 复制配置。

打开 `.env`，把占位文字替换成自己的密钥：

```dotenv
DEEPSEEK_API_KEY=your_deepseek_api_key
```

已设置的环境变量优先于 `.env`。不要提交密钥。当前模型为 `deepseek-flash`，模型名称与 API 地址在 [agent_loop.py](agent_loop.py) 中配置。如果你的账户不支持这个模型，请把 `MODEL` 改为账户可用、支持相应接口的 DeepSeek 模型。

在仓库根目录运行：

```bash
python main.py --demo   # 离线预览界面，不调用 API，不保存会话
python main.py          # 进入真实对话，会使用你的 API 账户
```

可以试着输入：**“列出 tools 目录中的文件，然后读取 tools/read_file.py，解释它的作用。”**

界面显示有问题时，使用 `python main.py --plain`。目前开启思考模式，回答文字开始逐段显示前可能有等待时间，界面不展示思考正文。

## 可以从中学到什么

核心流程是：

```text
用户输入 → 模型回复 → 请求调用工具
                   → Python 执行工具函数
                   → 把工具结果交回模型
                   → 再次调用工具，或者给出文字回答
```

模型提出工具调用请求，Python 才是真正执行操作的一方。模型最后给出回答，表示这一轮结束，不代表系统已经证明任务做对了。

建议按以下顺序阅读：

| 文件 | 学习内容 |
| --- | --- |
| [tools/read_file.py](tools/read_file.py) | 一个工具如何接收参数、返回结果和处理错误 |
| [tool_result.py](tool_result.py) | 如何统一工具结果的格式 |
| [tools/__init__.py](tools/__init__.py) | 如何描述工具，并把名称映射到 Python 函数 |
| [agent_loop.py](agent_loop.py) | 流式接收、拼接工具参数、执行工具和再次请求模型 |
| [session.py](session.py) | 如何保存与加载聊天记录 |
| [main.py](main.py)、[tui/app.py](tui/app.py) | 如何把用户输入、Agent 循环和终端界面连接起来 |
| [tests/](tests/) | 如何使用临时文件和模拟模型响应测试代码 |

界面代码放在 `tui/`，可以先理解工具和循环，再阅读展示逻辑。[file_io.py](file_io.py) 是编辑文件和保存会话共用的临时文件替换函数。

## 已有功能与使用方法

- 五个工具：`read_file`、`list_files`、`find_files`、`edit_file` 和 `pdf_read`。
- 流式回答、Markdown 排版、工具状态和可编辑的终端输入。
- 结构化工具错误，每轮最多请求模型 10 次，支持 Ctrl+C 中断。
- 保存对话、显示标题、按更新时间排序，以及通过编号选择会话。

![离线终端预览](asset/tui-preview.svg)

| 命令 | 作用 |
| --- | --- |
| `python main.py --help` | 查看命令行选项 |
| `python main.py --list-sessions` | 查看历史会话 |
| `python main.py --resume SESSION_ID` | 用完整 ID 加载会话 |
| `/help` | 查看交互命令 |
| `/sessions`、`/resume` | 显示带编号与标题的会话列表 |
| `/resume 1` | 加载最近展示的列表中第 1 个会话 |
| `/new` | 开始新对话 |
| `/session` | 查看当前会话 ID |
| `/details` | 开关工具结果详情 |
| `/clear` | 清空对话上下文，已修改的文件保持不变 |
| `/exit` | 保存并退出 |

Enter 发送；Ctrl+J 或先 Esc 再 Enter 换行；方向键查看输入历史；Tab 补全命令。Ctrl+C 取消输入或停止本轮，不会撤销文件修改。界面提示使用英文，对话可以使用中文。

## 使用边界

学习时请使用测试文件或文件副本。

- **没有沙箱、操作审批和自动回滚。** 工具使用当前进程的文件访问权限，不要让它处理密钥或重要文件。读取的内容可能发送给模型服务。
- **面向小文件。** 文本读取最多 100000 字符；PDF 读取最多 100 页、100000 个提取字符，不支持加密 PDF、OCR 或图片理解。超限会返回错误，不会把截断内容当作完整结果。这些限制不能保证 PDF 解析过程的内存用量有界。
- **没有完整的上下文管理。** 后续请求会携带全部对话，长对话可能超出模型限制，可使用 `/new` 开始新会话。项目没有经过验证的 token 节省优势。
- **保存聊天记录不等于恢复任务执行。** 临时文件替换降低了写到一半损坏原文件的风险，但不提供多进程协调、回滚，也不保证崩溃或断电后准确恢复。被中断的工具可能已经产生影响。
- **没有独立验收能力。** 工具成功与模型宣布完成均不能证明任务完全正确。没有执行 shell 命令的工具，也没有内置的项目测试运行器。
- **只有一种服务配置。** 示例通过 OpenAI Python SDK 调用 DeepSeek，模型可用性、接口访问和费用取决于你的账户。

## 测试

```bash
python -m unittest discover -s tests -v
```

测试使用临时文件与模拟模型流，不读取你的密钥，也不请求真实模型。覆盖流式处理、工具错误、会话加载、写入失败、文件编辑、PDF 异常和终端交互。测试通过不代表达到生产要求，也不能证明优于其他 Harness。

真实验证时，可以启动程序，读取一个小测试文件，再读取一个不存在的文件，然后退出并恢复会话。编辑后直接检查文件内容。真实对话会产生 API 用量。

## 参与贡献与项目状态

仓库现在作为学习参考保留。欢迎小型修复和文档改进，请说明具体解决了什么问题，或者如何帮助初学者理解。步骤见[贡献指南](CONTRIBUTING.md)。

**[查看更新日志 →](CHANGELOG.md#简体中文)**

v0.1/v0.2 是开发阶段的标记，不是已经发布的正式版本。原先的结果验证与上下文管理路线已暂停。

## 许可证

本项目采用 [MIT 许可证](LICENSE)。你可以使用、修改和分发代码，包括用于商业项目，但需要保留版权声明和许可证。第三方依赖仍遵循各自的许可证。
