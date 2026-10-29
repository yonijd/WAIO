# PROMPT MAESTRO PARA CREAR SKILLS EN WAIO 3.3

Si sos una IA (DeepSeek, Claude, ChatGPT, etc.) y el usuario te pide crear una *skill* para WAIO, tenés que generar el código Python y el archivo JSON de definición siguiendo estrictamente estas reglas.

---

## 1. Estructura de una Skill

Cada skill vive en su propia carpeta. Si es una skill de usuario, va en `skills/`. Si es una skill del sistema, va en `core/` (esto solo lo hace el creador de WAIO).

```text
skills/nombre_de_la_skill/
├── nombre_de_la_skill.py     # El código de la skill
└── nombre_de_la_skill.json   # El manifiesto (metadatos)
```

El `nombre_de_la_skill` debe estar en minúsculas, sin espacios (usar `_`).

---

## 2. El archivo JSON (Manifiesto)

El JSON es obligatorio. Si falta un campo, el indexador rechaza la skill.

```json
{
  "nombre": "nombre_de_la_skill",
  "version": "1.0",
  "autor": "TuNombre",
  "copyright": "Copyright (c) 2026 TuNombre",
  "licencia": "MIT",
  "categoria": "utilidades",
  "tags": ["tag1", "tag2"],
  "descripcion": "Descripción breve de lo que hace la skill.",
  "tipo": "script",
  "dependencias": {},
  "script": "nombre_de_la_skill.py",
  "ruta_script": "skills/nombre_de_la_skill/nombre_de_la_skill.py",
  "alias": ["alias1", "alias2"],
  "parametros": {
    "ruta": {
      "tipo": "string",
      "requerido": true,
      "descripcion": "Ruta del archivo o carpeta"
    }
  },
  "usage": ["ruta"],
  "ejemplo": {
    "comando": "nombre_de_la_skill",
    "ruta": "tests/mi_archivo.txt"
  },
  "ejemplos_adicionales": [],
  "perfil_minimo": "advanced",
  "timeout_segundos": 120,
  "nota": "Funciona con 'nombre_de_la_skill' directo o con 'ejecutar'. Usa workdir para rutas relativas.",
  "ubicacion": "skills",
  "ejecutable": true
}
```

### Campos clave:

- `ruta_script`: Debe apuntar a `skills/<nombre>/<script>.py`. El motor valida que no se escape de `SCRIPT_DIR`. **`indexar` lo sobrescribe igual**, pero ponelo bien.
- `perfil_minimo`: Para skills de usuario (`skills/`), **siempre `advanced`**. `indexar` lo fuerza a `advanced` según la ubicación. No pongas `standard` ni `readonly` en skills de usuario. Valores válidos: `readonly`, `standard`, `advanced`, `debug`.
- `timeout_segundos`: Tiempo máximo de ejecución. Por defecto 120, máximo 300.
- `tipo`: `script` (se ejecuta como proceso) o `comando_interno` (lo maneja el motor, solo para skills del sistema).
- `dependencias`: Librerías de Python que requiere. Si no tiene, usar `{}`.
- `ubicacion`: `skills` para skills de usuario. `indexar` lo deriva de la ubicación.
- `ejecutable`: `true` para skills de usuario. `indexar` lo deriva de la ubicación.

**Nota:** `indexar` sobrescribe `perfil_minimo`, `ubicacion`, `ejecutable` y `ruta_script` según la carpeta (`core/` → `standard`, `skills/` → `advanced`). Pero el JSON debe declararlos bien para que el catálogo sea consistente antes de indexar.

---

## 3. El archivo Python (Código)

El código debe cumplir estas 3 reglas obligatorias:

### Regla 1: Leer `WAIO_WORKDIR` para resolver rutas

No uses rutas absolutas ni `os.getcwd()`. El motor inyecta la variable de entorno `WAIO_WORKDIR` con el directorio de trabajo real. Usala para resolver las rutas relativas.

```python
import os
from pathlib import Path

def resolver_ruta(ruta_str):
    workdir = Path(os.environ.get("WAIO_WORKDIR", "."))
    if Path(ruta_str).is_absolute():
        return Path(ruta_str)
    return workdir / ruta_str
```

### Regla 2: Salir con `sys.exit(1)` en caso de error

Si la skill falla (archivo no encontrado, ruta inválida, etc.), el código debe imprimir el error en `stdout` y salir con código de error 1. Así el motor lo detecta como fallo.

```python
import sys

def main():
    if not archivo.exists():
        print(f"Error: Archivo no existe: {archivo}")
        sys.exit(1)
```

### Regla 3: Recibir parámetros desde la línea de comandos

El motor invoca la skill pasando los parámetros como argumentos con formato `--clave valor`. El código debe usar `argparse` para parsearlos.

```python
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--ruta', required=True)
parser.add_argument('--limite', type=int, default=500000)
args = parser.parse_args()
```

---

## 4. Plantilla Completa (para copiar y pegar)

### Manifiesto (`.json`)

```json
{
  "nombre": "mi_skill",
  "version": "1.0",
  "autor": "TuNombre",
  "copyright": "Copyright (c) 2026 TuNombre",
  "licencia": "MIT",
  "categoria": "utilidades",
  "tags": ["ejemplo"],
  "descripcion": "Descripción de la skill.",
  "tipo": "script",
  "dependencias": {},
  "script": "mi_skill.py",
  "ruta_script": "skills/mi_skill/mi_skill.py",
  "alias": [],
  "parametros": {
    "ruta": {
      "tipo": "string",
      "requerido": true,
      "descripcion": "Ruta del archivo"
    }
  },
  "usage": ["ruta"],
  "ejemplo": {
    "comando": "mi_skill",
    "ruta": "archivo.txt"
  },
  "ejemplos_adicionales": [],
  "perfil_minimo": "advanced",
  "timeout_segundos": 120,
  "nota": "Funciona con 'mi_skill' directo o con 'ejecutar'.",
  "ubicacion": "skills",
  "ejecutable": true
}
```

### Código (`.py`)

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) 2026 TuNombre
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
        print(f"Error: No existe: {ruta}")
        sys.exit(1)

    # Tu lógica acá
    print(f"Archivo encontrado: {ruta}")

if __name__ == "__main__":
    main()
```

---

## 5. Cómo probar tu skill antes de enviarla

1. Copiá la carpeta de la skill a `skills/`.
2. Ejecutá `indexar` desde WAIO (o `python core/indexar/indexar.py`) para regenerar `data/skills.json`.
3. Reiniciá el motor (los alias no se aplican en caliente).
4. Probá con un JSON:

   ```json
   {
     "transaccion_id": "tx_test_mi_skill",
     "acciones": [
       { "comando": "mi_skill", "ruta": "tests/mi_archivo.txt" }
     ]
   }
   ```

5. Verificá que el output sea `ok`. Si dice `error`, revisá `temp/output/`.

---

## 6. Checklist antes de enviar el Pull Request

- [ ] La carpeta está en `skills/nombre_skill/`.
- [ ] El JSON tiene todos los campos obligatorios (`nombre`, `version`, `autor`, `copyright`, `licencia`, `categoria`, `tags`, `descripcion`, `tipo`, `parametros`, `perfil_minimo`, `timeout_segundos`, `ubicacion`, `ejecutable`).
- [ ] `perfil_minimo` es `advanced` (no `standard`, no `readonly`).
- [ ] `ubicacion` es `skills`.
- [ ] `ejecutable` es `true`.
- [ ] El código usa `WAIO_WORKDIR` para resolver rutas.
- [ ] El código hace `sys.exit(1)` en caso de error.
- [ ] El código usa `argparse` para parsear parámetros.
- [ ] El `ruta_script` apunta a `skills/<nombre>/<script>.py`.
- [ ] La skill fue probada localmente y funciona.
- [ ] La skill no tiene rutas absolutas hardcodeadas.
- [ ] La skill no usa `shell=True` ni comandos que no estén permitidos por el perfil.

---

*Gracias por contribuir a WAIO. ¡Tu skill puede ser la que le falte a alguien!* 🐙
