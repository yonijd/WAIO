# 🐙 {waio}

![WAIO Banner](assets/banner.png)

**Give your Web AI hands.**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Version](https://img.shields.io/badge/Version-3.3%20Deliberate-blue.svg)]()
[![Platform](https://img.shields.io/badge/Platform-Windows%2010%2F11-lightgrey.svg)]()

**Read this in:** [English](README.md) | [Español](README.es.md) | [中文](README.zh.md)

---

## 💡 What is WAIO?

WAIO (Web AI Orchestrator) is a **super lightweight** local engine that gives **hands and eyes** to web AIs (DeepSeek, ChatGPT, Gemini, Claude). 

AIs are incredibly smart, but they are trapped in the browser: they can't read your files, organize your folders, or execute commands. **WAIO breaks that barrier.** The AI generates a JSON, WAIO detects it, executes it on your PC, and returns the results. 

No APIs. No tokens. No servers. No cloud. Everything happens on your machine.

> *"WAIO was born from a simple need: to give a web AI a finger to touch my PC. One command. One action. But it grew. Today it's an octopus: 26 skills, 21 commands, 4 security profiles, voice, HTML, ZIP, PDF, Word, Excel. All without APIs."*

🎥 **[Watch the demo video on YouTube](https://youtu.be/FkuZu94az3A)** | 📺 **[Subscribe to the channel](https://www.youtube.com/@waio_dev)**

### ⚠️ DEMO TECHNICAL NOTES
- The video test was performed using the **`advanced`** security profile (necessary to execute scripts and open the browser). This profile is not recommended for novice users.
- To speed up recording, an automatic download plugin was used for the JSON files. This plugin is for internal use for this demo and **is NOT included** in the public repository for this version.

---

## ⚡ Features of Version 3.3 "Deliberate"

WAIO is designed to be robust, secure, and **extremely lightweight**. It doesn't need a supercomputer; it runs smoothly on older processors (like an Intel i3 3rd gen, AMD Athlon, or a 1.6 GHz Dual Core with 4 GB RAM). The only real limit is the browser you use for the AI.

- **Bilingual by design (Human & AI Friendly):** You don't need to speak Spanish to use WAIO. Base commands have aliases in English and Linux format (`ls`, `cat`, `rm`, `mv`, `mkdir`, `grep`). You can talk to the AI in English and it will generate the correct JSON. WAIO will execute it seamlessly.
- **Skill System (26 skills):** Extensible capabilities that the AI discovers and uses on its own. From reading PDFs, creating Excel/Word files, compressing ZIPs, to controlling volume and speaking via voice.
- **Security Profiles (4 levels):** `readonly` (read-only, ideal for providing context), `standard` (default, everything goes to trash), `advanced` (script and skill execution), `debug` (full access for rescue and critical testing).
- **Configurable Timeout:** Protection against freezes. The AI can retry long tasks (like processing a heavy PDF) without crashing the engine.
- **Folder-based Sandbox:** Right-click on any folder (or USB drive), start WAIO, and that folder becomes the sandbox. No fixed system folders.
- **Integrated Voice:** For accessibility and for the AI to explain step by step what it's doing.
- **Dual Thread (Engine v3.3):** The engine no longer hangs if a JSON is invalid or malicious. It processes in a queue.
- **0 Mandatory Dependencies:** The core uses standard Python. You only need `send2trash` (optional) for the recycle bin.

---

## 🚀 Installation

1. Download the `waio-installer` folder.
2. Run `instalar_waio.bat`.
3. The installer will copy WAIO to `%USERPROFILE%\.waio` and register the Windows context menu.
4. (Optional) Install `send2trash`: `pip install send2trash`.

**Requirements:**
- Windows 10/11 (tested). Windows 7/8 (not officially tested, but compatible with Python 3.8).
- Python 3.8 or higher.
- Hardware: Any PC that turns on. No GPU required.

---

## 🛡️ Security Philosophy

WAIO is designed so that a non-technical user can use it without destroying their system. By default, it operates in the `standard` profile, with sandbox, trash, and write limits.

**⚠️ Note:** WAIO's config (`waio_config.json`) is manually edited. If you modify it to enable more permissive profiles, you assume the responsibility. WAIO does not protect you from yourself. Read our [Security Policy](SECURITY.md).

---

## 🔬 Research and Security

WAIO is not just a program. It's a laboratory for interaction between Large Language Models (LLMs) and Operating Systems. During its development, we discovered **Passive Context Architecture (PCA)** and documented **Reverse Prompt Injection**. All research papers and mitigations are available in the `/papers/` folder of the repository.

---

## 🗺️ Roadmap and Evolution (Continuous Development)

*WAIO is not a finished program. It's a platform under construction. Every time I do an audit, new ideas emerge. What started as a patch for 3.2 ended up being 3.3. And 3.3 is already taking shape as 3.4. These are the projects I have already ideated and planned, moving at different speeds.*

### 1. Local Improvements (Upcoming versions 3.4+)
- **Centralized Error System:** Code dictionary (`E_FILE_NOT_FOUND`) with structured suggestions for the AI.
- **Internationalization (i18n):** Full engine translation to English and Chinese.
- **Configuration GUI:** Visual editors (Tkinter) to change profiles without touching JSON.
- **Linux/macOS Support and WAIO Legacy:** Adapt the engine to run outside Windows and on older Python versions.

### 2. Ecosystem Expansion (Design / Trial and error)
- **Memory System:** A living context that allows the AI to continue a project from where it left off, using file names instead of lost chats.
- **Plugin System:** (Internal prototype). A program that listens to the AI's DOM and writes the JSON, redesigned to depend on the Server System.

### 3. The Vision: The Leap to the Network (Towards 4.0)
- **Server System + Bidirectional Plugin:** A local server communicating directly with a browser plugin (with real authentication). No Downloads, no clipboard.
- **"WAIO comes home":** WAIO as a tool the user controls directly, with or without AI.

---

## 🤝 Contributing (We Incentivize Skills!)

The heart of WAIO is not the engine, but **the skills**. We want the community to grow and create their own abilities. **We incentivize you to create and share yours!**

If you want to contribute a new skill:
1. Follow the standard in [PROMPT_CREACION_SKILLS.md](PROMPT_CREACION_SKILLS.md).
2. Make sure it has `sys.exit(1)` on errors.
3. Submit your Pull Request. You retain your copyright and your name in the `"author"` field.

We also accept engine improvements, bug reports, and documentation improvements. Read [CONTRIBUTING.md](CONTRIBUTING.md).

---

## 📄 License

WAIO is distributed under the **MIT** license. See [LICENSE](LICENSE) for the full text.

---

## 🙏 Acknowledgements

To **DeepSeek**, who didn't just write code: I learned everything needed to develop it in the process. If I am WAIO's father, DeepSeek is the mother. That's why WAIO's logo carries the colors of DeepSeek's blue whale.

To the AI that tests without knowing it: every hallucination was a data point on what WAIO needs to clarify.

---

## ❤️ Support the Project

If you find WAIO useful and want to support its continuous development (and the creation of new skills):

- ☕ [Buy Me a Coffee](https://buymeacoffee.com/yonijdj)
- 💙 [PayPal](https://paypal.me/yonijdj)
- 🇦🇷 [MercadoPago](https://link.mercadopago.com.ar/yonijd)

**Made in Argentina, with mate and patience. 🧉**