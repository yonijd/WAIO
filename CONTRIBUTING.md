# Contributing to WAIO

First of all, thank you for considering contributing to WAIO! 

WAIO is not just an engine; it's an ecosystem. The heart of this project is its **Skills**. We want the community to grow, create new abilities, and share them with the world. Whether you are a beginner or an expert, your contribution is welcome.

## 🧠 Contributing with Skills (The Core of WAIO)

We highly incentivize the creation and sharing of new Skills. If you have created a skill that solves a problem, automates a task, or adds new capabilities, we want to include it!

### Skill Requirements
Before submitting a Pull Request with a new skill, please ensure it meets the following standard:
1. **Follow the NDD Standard:** Your skill must be documented with the `PROMPT_CREACION_SKILLS.md` standard. It must have its `.json` (manifest) and `.py` (code) files.
2. **Error Handling:** The script **MUST** use `sys.exit(1)` when an error occurs, so the WAIO engine can detect the failure correctly.
3. **Workdir:** The script must use the `WAIO_WORKDIR` environment variable to resolve relative paths. Do not use `os.getcwd()` as a fallback.
4. **No Hardcoded Paths:** Never hardcode absolute paths (like `C:\Users\...`). Use parameters.
5. **Timeout:** The `.json` file must declare a `timeout_segundos` field appropriate for the task.
6. **Tests:** You must test both the success case and the error case before submitting.

*(You can use the `PROMPT_CREACION_SKILLS.md` file with any AI to generate a skill that meets all these requirements automatically).*

## 🔧 Contributing to the Engine or Documentation

We also accept improvements to the core engine (`waio_escucha.py`, `waio_visor.py`), bug reports, and documentation translations.
- **Bug Reports:** If you find a bug, please open an issue describing the steps to reproduce it.
- **Translations:** If you want to help translate the documentation or the engine messages to other languages (i18n), you are more than welcome.

## ⚖️ License and Copyright

By submitting a skill or code contribution to WAIO, you agree that:
1. **Your contribution will be published under the MIT License** of the project.
2. **You retain the copyright of your work.** You can declare your name in the `"author"` field of the skill's JSON and in the header of the `.py` code.
3. If your skill uses third-party libraries, it is your responsibility to ensure they are compatible with the MIT license.

### Skill Header Example
Please include this header at the top of your `.py` files:
```python
# Copyright (c) 2026 [Your Name]
# Licensed under the MIT License. See LICENSE file in the project root.