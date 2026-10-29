# 🐙 {waio}

![WAIO Banner](assets/banner.png)

**赋予你的网页AI一双手。**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Version](https://img.shields.io/badge/Version-3.3%20Deliberate-blue.svg)]()
[![Platform](https://img.shields.io/badge/Platform-Windows%2010%2F11-lightgrey.svg)]()

**Read this in:** [English](README.md) | [Español](README.es.md) | [中文](README.zh.md)

---

## 💡 什么是 WAIO？

WAIO (Web AI Orchestrator) 是一个**超轻量级**的本地引擎，为网页AI (DeepSeek, ChatGPT, Gemini, Claude) 赋予了**双手和眼睛**。

AI 极其聪明，但它们被困在浏览器中：无法读取你的文件、整理你的文件夹或执行命令。**WAIO 打破了这一壁垒。** AI 生成 JSON，WAIO 检测到它，在你的电脑上执行，并将结果返回给 AI。

无需 API。无需 Token。无需服务器。无需云端。一切都在你的机器上运行。

> *"WAIO 源于一个简单的需求：给网页AI一根手指去触碰我的电脑。一个命令。一个动作。但它成长了。今天它是一只章鱼：26项技能，21个命令，4种安全配置文件，语音，HTML，ZIP，PDF，Word，Excel。全部无需 API。"*

🎥 **[在 YouTube 上观看演示视频](https://youtu.be/FkuZu94az3A)** | 📺 **[订阅频道](https://www.youtube.com/@waio_dev)**

### ⚠️ 演示技术说明
- 视频测试使用的是 **`advanced`** 安全配置文件（执行脚本和打开浏览器所必需）。此配置文件不建议新手用户使用。
- 为了加快录制速度，JSON 文件使用了自动下载插件。该插件仅供本次演示内部使用，**不包含**在此版本的公共存储库中。

---

## ⚡ 版本 3.3 "Deliberate" 的功能

WAIO 的设计目标是稳健、安全且**极其轻量**。它不需要超级计算机；它可以在较旧的处理器上流畅运行（例如第 3 代 Intel i3、AMD Athlon 或 1.6 GHz 双核 4 GB RAM）。唯一的真正限制是你用于 AI 的浏览器。

- **双语设计（人类与 AI 友好）：** 你不需要会说西班牙语就能使用 WAIO。基础命令具有英语和 Linux 格式的别名（`ls`、`cat`、`rm`、`mv`、`mkdir`、`grep`）。你可以用英语与 AI 交谈，它会生成正确的 JSON。WAIO 将无缝执行。
- **技能系统（26项技能）：** AI 可以发现并自行使用的可扩展能力。从读取 PDF、创建 Excel/Word 文件、压缩 ZIP，到控制音量和语音播报。
- **安全配置文件（4个级别）：** `readonly`（只读，非常适合提供上下文），`standard`（默认，所有内容进入回收站），`advanced`（脚本和技能执行），`debug`（用于救援和关键测试的完全访问权限）。
- **可配置超时：** 防止卡死。AI 可以重试长任务（如处理大型 PDF）而不会导致引擎崩溃。
- **基于文件夹的沙盒：** 右键单击任何文件夹（或 U 盘），启动 WAIO，该文件夹即成为沙盒。没有固定的系统文件夹。
- **集成语音：** 用于无障碍访问，并让 AI 逐步解释它正在做什么。
- **双线程（引擎 v3.3）：** 如果 JSON 无效或恶意，引擎不再挂起。它会在队列中处理。
- **0 强制依赖：** 核心使用标准 Python。你只需要 `send2trash`（可选）用于回收站。

---

## 🚀 安装

1. 下载 `waio-installer` 文件夹。
2. 运行 `instalar_waio.bat`。
3. 安装程序会将 WAIO 复制到 `%USERPROFILE%\.waio` 并注册 Windows 上下文菜单。
4. （可选）安装 `send2trash`：`pip install send2trash`。

**要求：**
- Windows 10/11（已测试）。Windows 7/8（未正式测试，但与 Python 3.8 兼容）。
- Python 3.8 或更高版本。
- 硬件：任何能开机的电脑。无需 GPU。

---

## 🛡️ 安全理念

WAIO 的设计使得非技术用户可以在不破坏系统的情况下使用它。默认情况下，它以 `standard` 配置文件运行，带有沙盒、回收站和写入限制。

**⚠️ 注意：** WAIO 的配置文件 (`waio_config.json`) 是手动编辑的。如果你修改它以启用更宽松的配置文件，你将承担相应责任。WAIO 不能保护你免受自己的伤害。请阅读我们的 [安全政策](SECURITY.md)。

---

## 🔬 研究与安全

WAIO 不仅仅是一个程序。它是大型语言模型 (LLM) 与操作系统之间交互的实验室。在其开发过程中，我们发现了**被动上下文架构 (PCA)** 并记录了**反向提示注入**。所有研究论文和缓解措施均可在存储库的 `/papers/` 文件夹中找到。

---

## 🗺️ 路线图与演进（持续开发中）

*WAIO 不是一个完成的程序。它是一个正在建设中的平台。每次进行审计时，都会涌现新的想法。最初只是 3.2 的补丁，最终变成了 3.3。而 3.3 已经在向 3.4 迈进。这些是我已经构思并计划好的项目，以不同的速度推进。*

### 1. 本地改进（即将推出的版本 3.4+）
- **集中式错误系统：** 代码字典 (`E_FILE_NOT_FOUND`)，为 AI 提供结构化建议。
- **国际化 (i18n)：** 将引擎完整翻译为英语和中文。
- **配置 GUI：** 可视化编辑器 (Tkinter)，无需接触 JSON 即可更改配置文件。
- **Linux/macOS 支持与 WAIO Legacy：** 调整引擎以在 Windows 之外以及较旧的 Python 版本上运行。

### 2. 生态系统扩展（设计 / 试错）
- **记忆系统：** 一种活生生的上下文，允许 AI 使用文件名而不是丢失的聊天记录，从上次中断的地方继续项目。
- **插件系统：**（内部原型）。一个监听 AI 的 DOM 并写入 JSON 的程序，重新设计为依赖于服务器系统。

### 3. 愿景：向网络的飞跃（迈向 4.0）
- **服务器系统 + 双向插件：** 一个本地服务器，直接与浏览器插件通信（具有真实身份验证）。无需下载，无需剪贴板。
- **"WAIO 回家"：** WAIO 作为用户直接控制的工具，无论有没有 AI。

---

## 🤝 贡献（我们激励技能！）

WAIO 的核心不是引擎，而是**技能**。我们希望社区成长并创造自己的能力。**我们激励你创造并分享你的技能！**

如果你想贡献新技能：
1. 遵循 [PROMPT_CREACION_SKILLS.md](PROMPT_CREACION_SKILLS.md) 中的标准。
2. 确保在错误时包含 `sys.exit(1)`。
3. 提交你的 Pull Request。你保留你的版权，并在 `"author"` 字段中保留你的名字。

我们也接受引擎改进、错误报告和文档改进。请阅读 [CONTRIBUTING.md](CONTRIBUTING.md)。

---

## 📄 许可证

WAIO 在 **MIT** 许可证下分发。请参阅 [LICENSE](LICENSE) 获取完整文本。

---

## 🙏 致谢

致 **DeepSeek**，它不仅仅是编写代码：我在这个过程中学会了开发所需的一切。如果我是 WAIO 的父亲，DeepSeek 就是母亲。这就是为什么 WAIO 的标志带有 DeepSeek 蓝鲸的颜色。

致那些在不知不觉中进行测试的 AI：每一次幻觉都是关于 WAIO 需要澄清什么的数据点。

---

## ❤️ 支持项目

如果你觉得 WAIO 有用，并希望支持其持续发展（以及新技能的创造）：

- ☕ [Buy Me a Coffee](https://buymeacoffee.com/yonijdj)
- 💙 [PayPal](https://paypal.me/yonijdj)
- 🇦🇷 [MercadoPago](https://link.mercadopago.com.ar/yonijd)

**阿根廷制造，带着马黛茶和耐心。 🧉**