# MASTER PROMPT FOR CREATING SKILLS IN WAIO 3.3

If you are an AI (DeepSeek, Claude, ChatGPT, etc.) and the user asks you to create a *skill* for WAIO, you must generate the Python code and the JSON definition file strictly following these rules.

---

## 1. Structure of a Skill

Each skill lives in its own folder. If it's a user skill, it goes in `skills/`. If it's a system skill, it goes in `core/` (this is only done by the WAIO creator).

```text
skills/skill_name/
├── skill_name.py     # The skill code
└── skill_name.json   # The manifest (metadata)
```

The `skill_name` must be lowercase, no spaces (use `_`).

---

## 2. The JSON File (Manifest)

The JSON is mandatory. If a field is missing, the indexer rejects the skill.

```json
{
  "nombre": "skill_name",
  "version": "1.0",
  "autor": "YourName",
  "copyright": "Copyright (c) 2026 YourName",
  "licencia": "MIT",
  "categoria": "utilities",
  "tags": ["tag1", "tag2"],
  "descripcion": "Brief description of what the skill does.",
  "tipo": "script",
  "dependencias": {},
  "script": "skill_name.py",
  "ruta_script": "skills/skill_name/skill_name.py",
  "alias": ["alias1", "alias2"],
  "parametros": {
    "ruta": {
      "tipo": "string",
      "requerido": true,
      "descripcion": "Path of the file or folder"
    }
  },
  "usage": ["ruta"],
  "ejemplo": {
    "comando": "skill_name",
    "ruta": "tests/my_file.txt"
  },
  "ejemplos_adicionales": [],
  "perfil_minimo": "advanced",
  "timeout_segundos": 120,
  "nota": "Works with 'skill_name' directly or with 'ejecutar'. Uses workdir for relative paths.",
  "ubicacion": "skills",
  "ejecutable": true
}
```

### Key fields:

- `ruta_script`: Must point to `skills/<name>/<script>.py`. The engine validates that it doesn't escape `SCRIPT_DIR`. **`indexar` overwrites it anyway**, but set it correctly.
- `perfil_minimo`: For user skills (`skills/`), **always `advanced`**. `indexar` forces it to `advanced` based on location. Do not use `standard` or `readonly` in user skills. Valid values: `readonly`, `standard`, `advanced`, `debug`.
- `timeout_segundos`: Maximum execution time. Default 120, maximum 300.
- `tipo`: `script` (runs as a process) or `comando_interno` (handled by the engine, system skills only).
- `dependencias`: Python libraries required. If none, use `{}`.
- `ubicacion`: `skills` for user skills. `indexar` derives it from the location.
- `ejecutable`: `true` for user skills. `indexar` derives it from the location.

**Note:** `indexar` overwrites `perfil_minimo`, `ubicacion`, `ejecutable` and `ruta_script` based on the folder (`core/` → `standard`, `skills/` → `advanced`). But the JSON must declare them correctly so the catalog is consistent before indexing.

---

## 3. The Python File (Code)

The code must comply with these 3 mandatory rules:

### Rule 1: Read `WAIO_WORKDIR` to resolve paths

Do not use absolute paths or `os.getcwd()`. The engine injects the `WAIO_WORKDIR` environment variable with the real working directory. Use it to resolve relative paths.

```python
import os
from pathlib import Path

def resolver_ruta(ruta_str):
    workdir = Path(os.environ.get("WAIO_WORKDIR", "."))
    if Path(ruta_str).is_absolute():
        return Path(ruta_str)
    return workdir / ruta_str
```

### Rule 2: Exit with `sys.exit(1)` on error

If the skill fails (file not found, invalid path, etc.), the code must print the error to `stdout` and exit with error code 1. That way the engine detects it as a failure.

```python
import sys

def main():
    if not archivo.exists():
        print(f"Error: File does not exist: {archivo}")
        sys.exit(1)
```

### Rule 3: Receive parameters from the command line

The engine invokes the skill passing parameters as arguments in `--key value` format. The code must use `argparse` to parse them.

```python
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--ruta', required=True)
parser.add_argument('--limite', type=int, default=500000)
args = parser.parse_args()
```

---

## 4. Complete Template (copy and paste)

### Manifest (`.json`)

```json
{
  "nombre": "my_skill",
  "version": "1.0",
  "autor": "YourName",
  "copyright": "Copyright (c) 2026 YourName",
  "licencia": "MIT",
  "categoria": "utilities",
  "tags": ["example"],
  "descripcion": "Skill description.",
  "tipo": "script",
  "dependencias": {},
  "script": "my_skill.py",
  "ruta_script": "skills/my_skill/my_skill.py",
  "alias": [],
  "parametros": {
    "ruta": {
      "tipo": "string",
      "requerido": true,
      "descripcion": "File path"
    }
  },
  "usage": ["ruta"],
  "ejemplo": {
    "comando": "my_skill",
    "ruta": "file.txt"
  },
  "ejemplos_adicionales": [],
  "perfil_minimo": "advanced",
  "timeout_segundos": 120,
  "nota": "Works with 'my_skill' directly or with 'ejecutar'.",
  "ubicacion": "skills",
  "ejecutable": true
}
```

### Code (`.py`)

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) 2026 YourName
# Licensed under the MIT License. See LICENSE file in the project root.

import os
import sys
import argparse
from pathlib import Path

def resolver_ruta(ruta_str):
    workdir = Path(os.environ.get("WAIO_WORKDIR", "."))
    if Path(ruta_str).is_absolute():
        return Path(ruta_str)
    return workdir / ruta_str

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--ruta', required=True)
    args = parser.parse_args()

    ruta = resolver_ruta(args.ruta)

    if not ruta.exists():
        print(f"Error: Does not exist: {ruta}")
        sys.exit(1)

    # Your logic here
    print(f"File found: {ruta}")

if __name__ == "__main__":
    main()
```

---

## 5. How to test your skill before submitting

1. Copy the skill folder to `skills/`.
2. Run `indexar` from WAIO (or `python core/indexar/indexar.py`) to regenerate `data/skills.json`.
3. Restart the engine (aliases are not applied hot).
4. Test with a JSON:

   ```json
   {
     "transaccion_id": "tx_test_my_skill",
     "acciones": [
       { "comando": "my_skill", "ruta": "tests/my_file.txt" }
     ]
   }
   ```

5. Verify the output is `ok`. If it says `error`, check `temp/output/`.

---

## 6. Checklist before submitting the Pull Request

- [ ] The folder is in `skills/skill_name/`.
- [ ] The JSON has all mandatory fields (`nombre`, `version`, `autor`, `copyright`, `licencia`, `categoria`, `tags`, `descripcion`, `tipo`, `parametros`, `perfil_minimo`, `timeout_segundos`, `ubicacion`, `ejecutable`).
- [ ] `perfil_minimo` is `advanced` (not `standard`, not `readonly`).
- [ ] `ubicacion` is `skills`.
- [ ] `ejecutable` is `true`.
- [ ] The code uses `WAIO_WORKDIR` to resolve paths.
- [ ] The code calls `sys.exit(1)` on error.
- [ ] The code uses `argparse` to parse parameters.
- [ ] `ruta_script` points to `skills/<name>/<script>.py`.
- [ ] The skill was tested locally and works.
- [ ] The skill has no hardcoded absolute paths.
- [ ] The skill does not use `shell=True` or commands not allowed by the profile.

---

*Thanks for contributing to WAIO. Your skill might be the one someone else is missing!* 🐙