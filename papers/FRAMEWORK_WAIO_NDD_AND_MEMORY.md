# WAIO FRAMEWORK: NOMENCLATURE-DRIVEN DEVELOPMENT (NDD)
**Project:** WAIO (Web AI Orchestrator)
**Author:** Yonijd
**Date:** October 25, 2026
**Purpose:** To define the project structuring standard for autonomous agents based on Passive Context and Semantic Memory.

---

## 1. The Problem of the Static Prompt

In traditional programming (Python, C++, JS), we have folder standards (e.g., `/src`, `/bin`, `/tests`) and configuration files (`package.json`, `requirements.txt`).

In AI agent development (Skills, Plugins), the problem is that every time we create a new program, we have to rewrite or adapt the *System Prompt* to explain to the AI what the project is, what files it has, what rules it follows, and what its current state is. This is inefficient, burns tokens, and generates errors.

**The solution:** The **NDD Framework**. Instead of the human explaining the project to the AI in the prompt, the **file system itself IS the explanation**. The environment becomes the *implicit System Prompt*.

---

## 2. The NDD Standard (Nomenclature-Driven Development)

NDD proposes that the name of each folder and file be a syntactic instruction. For the development of new Skills in WAIO, the structure must dictate the behavior.

### A. The Workdir as a Memory System
For long projects, we do not need an SQL database. We use **Passive Semantic Memory**. The project's Workdir stores state files:

*   `current_phase_security_audit_state.txt`
*   `pending_optimize_voice_skill.txt`
*   `memory_the_ai_prefers_to_respond_in_json.txt`
*   `reminder_do_not_use_bootstrap_in_html.txt`

**What happens when a new AI enters?** It runs a `listia`. It reads those names. And it automatically **knows what state the project is in, what is missing, and what rules it must not break**, without reading a single file or spending context tokens.

### B. Skill Design by "Legos"
When we develop a new skill (e.g., `create_pdf`), instead of giving it usage instructions in the prompt, we create a micro-environment:

*   `rule_pdf_use_arial_12_font.txt`
*   `rule_pdf_margins_2_5_cm.txt`
*   `environment_pdf_print_mode_grayscale_scale.txt`

The AI builds the skill's logic by joining these context "legos." If the user wants to change the margin, they do not change the Python code; they simply rename the file to `margins_3_cm.txt`.

---

## 3. Application in Long Projects (Macro Context)

In multi-month projects, chats get lost and the AI forgets the context. With NDD, the directory becomes a **Living Logbook**.

### The Structure of an NDD Project:
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