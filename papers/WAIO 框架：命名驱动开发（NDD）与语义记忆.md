# WAIO 框架：命名驱动开发（NDD）
**项目：** WAIO（Web AI Orchestrator）
**作者：** Yonijd
**日期：** 2026 年 10 月 25 日
**目的：** 为基于被动上下文与语义记忆的自主代理定义项目结构化标准。

---

## 1. 静态提示词的问题

在传统编程（Python、C++、JS）中，我们有文件夹标准（如 `/src`、`/bin`、`/tests`）和配置文件（`package.json`、`requirements.txt`）。

在人工智能代理开发（技能、插件）中，问题在于：每次创建新程序时，我们都必须重写或调整*系统提示词*，向人工智能说明项目是什么、有哪些文件、遵循哪些规则以及当前状态如何。这效率低下、消耗 token 并产生错误。

**解决方案：** **NDD 框架**。与其由人类在提示词中向人工智能解释项目，不如让**文件系统本身成为解释**。环境成为*隐式系统提示词*。

---

## 2. NDD 标准（命名驱动开发）

NDD 提出：每个文件夹和文件的名称都应是一条句法指令。对于 WAIO 中新技能的开发，结构必须规定行为。

### A. 工作目录作为记忆系统
对于长期项目，我们不需要 SQL 数据库。我们使用**被动语义记忆**。项目的工作目录存储状态文件：

* `current_phase_security_audit_state.txt`
* `pending_optimize_voice_skill.txt`
* `memory_the_ai_prefers_to_respond_in_json.txt`
* `reminder_do_not_use_bootstrap_in_html.txt`

**当新的人工智能进入时会发生什么？** 它执行一次 `listia`。读取这些名称。然后自动**知道项目处于什么状态、缺少什么、不能违反哪些规则**，而无需读取任何文件或消耗上下文 token。

### B. 通过"乐高"设计技能
当我们开发新技能（如 `create_pdf`）时，不在提示词中给出使用说明，而是创建一个微环境：

* `rule_pdf_use_arial_12_font.txt`
* `rule_pdf_margins_2_5_cm.txt`
* `environment_pdf_print_mode_grayscale_scale.txt`

人工智能通过组合这些上下文"乐高"来构建技能逻辑。如果用户想更改页边距，无需修改 Python 代码；只需将文件重命名为 `margins_3_cm.txt`。

---

## 3. 在长期项目中的应用（宏观上下文）

在持续数月的项目中，聊天记录会丢失，人工智能会遗忘上下文。使用 NDD，目录成为一本**活的日志簿**。

### NDD 项目的结构：
```text
/proyecto_waio_skill_voz/
│
├── 00_CONTEXTO_GENERAL/
│   ├── objetivo_crear_skill_de_voz_con_tts_offline.txt
│   └── autor_usuario_principiante_sin_conocimientos_avanzados.txt
│
├── 01_ESTADO_ACTUAL/
│   ├── fase_1_completada_lectura_de_texto.txt
│   └── fase_2_pendiente_integracion_de_voces.txt
│
├── 02_REGLAS_ESTRICTAS/
│   ├── prohibido_usar_apos_nube_usar_offline.txt
│   └── ignorar_archivos_temporales_de_prueba.txt
│
└── 03_ASSETS/
    └── (imágenes, audios, etc.)