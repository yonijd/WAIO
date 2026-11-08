# CHANGELOG - WAIO

All notable changes to WAIO are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [v3.3 Deliberate] - 2026-10-17

Deep refactor of the engine, satellites, configuration and response system. Every decision is made consciously. Nothing is accidental.

### Added

- **`[SECTION]` response format**: replaces the flat format. Sections `[STATUS]`, `[COMANDO]`, `[RESULTADO]`, `[AVISO]`, `[SUSURRO]`, `[RECORDATORIO]`.
- **Configurable timeout at 3 levels**: action -> skill -> config. With maximum cap. Previously fixed at 60s.
- **`WAIO_WORKDIR` via environment variable**: the engine passes it to the skills. Fixes the `obtener_workdir` bug in 22 skills.
- **Processing order by ascending `mtime`**: processes the oldest JSON first.
- **Cache by `mtime`** in config, skills and wispout. Clean log.
- **Security actually implemented**: read/write limits enforced, validation of `destino` and `ruta_script`, normalized `carpetas_prohibidas`, detection of invalid `perfil_activo`.
- **System limits**: maximum actions per transaction, maximum transactions per minute, maximum files in `output/` and `jsonout/`.
- **`core/` structure**: base commands and main scripts moved to `core/` (one per folder). Added `core/voz`, `core/listia`, `core/ejecutar_comando`, etc.
- **Dual thread (Watcher + Processor)**: the engine now has a thread that scans `Downloads/` and moves to `temp/queue/`, and another that processes the queue. Prevents hangs.
- **Crash recovery**: if the engine closes mid-transaction, on startup it moves the JSONs from `temp/processing/` to `temp/jsonout/rechazados/` with an `.error.txt`.
- **Duplicate index**: the engine rejects `transaccion_id` that were already processed (configurable).
- **Blacklist of reserved names**: blocks `CON`, `NUL`, `PRN`, `AUX`, `COM1-9`, `LPT1-9` and the `:` character.
- **`transaccion_id` sanitization**: validates and replaces invalid characters before using it in file names.
- **`ejecutar_comando` as native command**: only available in `debug` profile, with command whitelist, blocking of `python -c`, `python -m`, pipes and redirections.
- **18 new fields** in `waio_config.json` (including `directorio_escucha`, `leer_json_en_downloads`, `aceptar_id_duplicado`).
- **`rescue_tools/` consolidated**: `kill_waio.py`, `limpiar_waio.py`, `ver_estado.py`, uninstaller, `README.md`.
- **`CONF`, `WISP` and `PROMPT` buttons** in the viewer.
- **`total_acciones`** set from the engine (fixes the v3.2 bug).
- **`pid_es_python`**: before killing the lock PID, verifies with `tasklist` that it is Python.

### Changed

- **Much larger engine**: from 65 KB to 74 KB. Includes cache, timeouts, limits and security.
- **`escucha_output.py`**: fix of `GlobalLock fallo` using `ctypes` with 3s timeout. Buffer ordered by `(transaccion_id, accion_idx)`.
- **`waio_visor.py`**: clipboard copy removed from `mostrar_json`. `CONF`, `WISP` and `PROMPT` buttons. Messages in English. Reads `visor_max_lines` and `visor_refresh_ms` from config.
- **Installer**: does NOT copy `temp/` (drags logs and junk). Does NOT copy `trash/` (the engine creates it). Creates empty `temp/`. `limpiar_entradas_viejas` deletes obsolete keys. `validar_src_dir` verifies it doesn't install over itself.
- **Uninstaller**: `borrar_clave_recursiva` to delete keys with subkeys. Preserves `trash/` and `temp/logs/` if the user requests it.
- **Context menu**: 4 entries (`04_clip_output` removed, `05_kill_waio` moved to `04_kill_waio`).
- **`wispout.json`**: completely new structure. Each section has rules (`activo`, `inicio_accion`, `duracion_acciones`, `cada_cuantas_acciones`, `repeticion_cada`, `mostrar_en_error`, `mostrar_en_primera`).
- **Profiles renamed**: `solo_lectura` -> `readonly`, `estandar` -> `standard`, `avanzado` -> `advanced`, `sin_restricciones` -> `debug`. Added `permite_ejecutar_core/skills/workdir/disco`.
- **`limite_lectura_bytes`** renamed to **`limite_lectura_chars`**.

### Fixed

- **`GlobalLock fallo`** in `copiar_portapapeles` (was a 64-bit handle bug).
- **`total_acciones`** not set from the engine.
- **Alias cache**: the mapping is now rebuilt with `construir_mapeo_comandos()`.
- **`obtener_workdir`** in 22 skills.
- **Alias collision**: `grep` removed from `buscar_contenido`, `info` removed from `skills`.
- **`ejecutar_comando` security**: `shell=True` removed, `python -c` and `python -m` blocked, pipes and redirections blocked, command whitelist.

### Notes

- Known bugs: see `REPORTE.md`.
- Pending:
  - Config and wispout GUIs (buttons prepared, no code).
  - `event_visor.py` unaudited.
  - Log rotation (`logs_retention_days: 7` in config but not applied).

---

## [v3.2 Structured] - 2026-09-04

Complete reorganization version. The project goes from having everything scattered to having everything in folders. Commands stop being code and become data.

### Added

- **Folder structure**: `config/`, `core/`, `data/`, `rescue_tools/`, `skills/`, `temp/`.
- **Base commands in `core/`**: each command is a folder with its JSON.
- **`core/indexar/indexar.py`**: independent indexer.
- **Unified commands**: `skills`, `indexar`, `ejecutar`, `ayuda`.
- **`rescue_tools/`**: kill_waio, stop_monitor, bats.
- **`LICENSE`**, **`requirements.txt`**, **`.gitignore`**.

### Changed

- **Installer**: copies entire folders instead of loose files.
- **Engine**: reads from `config/`, `data/`, `temp/`.

---

## [v3.1 Skilled] - 2026-07-29

Transition version. Introduces the skills system, configurable security profiles, WispOut and two auxiliary modules (`event_visor`, `speech`) that did not consolidate.

### Added

- Skills system in `habilidades/`.
- Profiles system in `waio_config.json`.
- WispOut: `wispout.json` with response format.
- Event Visor: event monitor with `watchdog`.
- Speech: voice reader.
- New commands: `append_archivo`, `renombrar_archivo`, `contar_lineas`, `leer_lineas`, `buscar_archivos`, `ejecutar_script`, `listar_habilidades`, `indexar_habilidades`.

### Notes

- Transition version. Not published as stable.

---

## [v3.0 Consolidated] - 2026-06-12

First version considered ready to publish. Focus on fixing bugs and security issues from v2.5, and on adding `escucha_output`.

### Added

- `escucha_output.py`: results compiler with 5s timeout.
- `mensaje` command.
- Editable prompt in `.waio/prompt.txt`.
- `ver_estado.bat` and `limpiar_waio.bat`.
- Numbered context menu (4 entries).
- `waio_version` field in the JSONs.

### Changed

- Engine renamed: `waio_escucha_v2.py` -> `waio_escucha.py`.
- Engine no longer writes to clipboard.
- Viewer: title fixed.
- LICENSE, requirements.txt added.

---

## [v2.5 Fluid] - 2026-06-12

Version focused on fluidity: frictionless input, larger reads, safe deletion and Unicode clipboard.

### Added

- TRANSCLIP (`transclip.py`).
- `trash/` folder.
- Real Unicode clipboard with `ctypes` UTF-16.
- Atomic JSON writing.

### Changed

- `MAX_READ_DEFAULT`: from 100k to 500k.
- Deletion commands: to Trash or `trash/`.

---

## [v2.0 Vision] - 2026-05-31

First publishable version. Conceptual leap from the previous proto-MCP.

### Added

- Main engine with 11 commands.
- JSON feedback in `output/`.
- Automatic clipboard copy.
- Tkinter viewer.
- Surgical kill switch.
- Installer, uninstaller and context menu.

---

## [Unreleased] - proto-MCP

Previous version without its own identity. Only 4 commands. Output only via log. Full code not preserved.