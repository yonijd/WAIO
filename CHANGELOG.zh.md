# CHANGELOG - WAIO

WAIO 的所有重要变更都记录在此文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)。

---

## [v3.3 深思熟虑] - 2026-10-17

对引擎、卫星、配置和响应系统进行深度重构。每个决定都是深思熟虑的。没有什么是偶然的。

### 新增

- **`[SECTION]` 响应格式**：替代扁平格式。区块 `[STATUS]`、`[COMANDO]`、`[RESULTADO]`、`[AVISO]`、`[SUSURRO]`、`[RECORDATORIO]`。
- **3 级可配置超时**：动作 -> 技能 -> 配置。带最大上限。之前固定为 60 秒。
- **通过环境变量传递 `WAIO_WORKDIR`**：引擎将其传递给技能。修复了 22 个技能中的 `obtener_workdir` 错误。
- **按 `mtime` 升序处理**：先处理最旧的 JSON。
- **按 `mtime` 缓存**：配置、技能和 wispout。日志干净。
- **真正实现的安全性**：应用读写限制、验证 `destino` 和 `ruta_script`、规范化 `carpetas_prohibidas`、检测无效的 `perfil_activo`。
- **系统限制**：每事务最大动作数、每分钟最大事务数、`output/` 和 `jsonout/` 中最大文件数。
- **`core/` 结构**：基础命令和主要脚本移至 `core/`（每个一个文件夹）。添加了 `core/voz`、`core/listia`、`core/ejecutar_comando` 等。
- **双线程（监视器 + 处理器）**：引擎现在有一个线程扫描 `Downloads/` 并移动到 `temp/queue/`，另一个处理队列。防止挂起。
- **崩溃恢复**：如果引擎在事务中途关闭，启动时将 JSON 从 `temp/processing/` 移动到 `temp/jsonout/rechazados/`，并附带 `.error.txt`。
- **重复索引**：引擎拒绝已处理过的 `transaccion_id`（可配置）。
- **保留名称黑名单**：阻止 `CON`、`NUL`、`PRN`、`AUX`、`COM1-9`、`LPT1-9` 和 `:` 字符。
- **`transaccion_id` 清理**：在用于文件名之前验证并替换无效字符。
- **`ejecutar_comando` 作为原生命令**：仅在 `debug` 配置文件中可用，带命令白名单、阻止 `python -c`、`python -m`、管道和重定向。
- **`waio_config.json` 中新增 18 个字段**（包括 `directorio_escucha`、`leer_json_en_downloads`、`aceptar_id_duplicado`）。
- **`rescue_tools/` 整合**：`kill_waio.py`、`limpiar_waio.py`、`ver_estado.py`、卸载程序、`README.md`。
- **查看器中的 `CONF`、`WISP` 和 `PROMPT` 按钮**。
- **`total_acciones`** 由引擎设置（修复 v3.2 的错误）。
- **`pid_es_python`**：在杀死锁 PID 之前，用 `tasklist` 验证它是 Python。

### 变更

- **引擎更大**：从 65 KB 到 74 KB。包括缓存、超时、限制和安全性。
- **`escucha_output.py`**：使用 `ctypes` 和 3 秒超时修复 `GlobalLock fallo`。缓冲区按 `(transaccion_id, accion_idx)` 排序。
- **`waio_visor.py`**：从 `mostrar_json` 移除剪贴板复制。`CONF`、`WISP` 和 `PROMPT` 按钮。英文消息。从配置读取 `visor_max_lines` 和 `visor_refresh_ms`。
- **安装程序**：不复制 `temp/`（拖拽日志和垃圾）。不复制 `trash/`（引擎创建它）。创建空的 `temp/`。`limpiar_entradas_viejas` 删除过时的键。`validar_src_dir` 验证不会安装在自身之上。
- **卸载程序**：`borrar_clave_recursiva` 删除带子键的键。如果用户要求，保留 `trash/` 和 `temp/logs/`。
- **上下文菜单**：4 个条目（移除 `04_clip_output`，`05_kill_waio` 改为 `04_kill_waio`）。
- **`wispout.json`**：全新的结构。每个区块都有规则（`activo`、`inicio_accion`、`duracion_acciones`、`cada_cuantas_acciones`、`repeticion_cada`、`mostrar_en_error`、`mostrar_en_primera`）。
- **配置文件重命名**：`solo_lectura` -> `readonly`、`estandar` -> `standard`、`avanzado` -> `advanced`、`sin_restricciones` -> `debug`。添加了 `permite_ejecutar_core/skills/workdir/disco`。
- **`limite_lectura_bytes`** 重命名为 **`limite_lectura_chars`**。

### 修复

- **`GlobalLock fallo`** 在 `copiar_portapapeles` 中（是 64 位句柄错误）。
- **`total_acciones`** 未从引擎设置。
- **别名缓存**：现在用 `construir_mapeo_comandos()` 重建映射。
- **`obtener_workdir`** 在 22 个技能中。
- **别名冲突**：`grep` 从 `buscar_contenido` 中移除，`info` 从 `skills` 中移除。
- **`ejecutar_comando` 安全性**：移除 `shell=True`，阻止 `python -c` 和 `python -m`，阻止管道和重定向，命令白名单。

### 备注

- 已知错误：见 `REPORTE.md`。
- 待办：
  - 配置和 wispout 的 GUI（按钮已准备，无代码）。
  - `event_visor.py` 未审计。
  - 日志轮换（配置中 `logs_retention_days: 7` 但未应用）。

---

## [v3.2 结构化] - 2026-09-04

完全重组版本。项目从一切散乱变为一切在文件夹中。命令不再是代码，而是数据。

### 新增

- **文件夹结构**：`config/`、`core/`、`data/`、`rescue_tools/`、`skills/`、`temp/`。
- **`core/` 中的基础命令**：每个命令是一个带 JSON 的文件夹。
- **`core/indexar/indexar.py`**：独立索引器。
- **统一命令**：`skills`、`indexar`、`ejecutar`、`ayuda`。
- **`rescue_tools/`**：kill_waio、stop_monitor、bats。
- **`LICENSE`**、**`requirements.txt`**、**`.gitignore`**。

### 变更

- **安装程序**：复制整个文件夹而不是零散文件。
- **引擎**：从 `config/`、`data/`、`temp/` 读取。

---

## [v3.1 熟练] - 2026-07-29

过渡版本。引入技能系统、可配置安全配置文件、WispOut 和两个未整合的辅助模块（`event_visor`、`speech`）。

### 新增

- `habilidades/` 中的技能系统。
- `waio_config.json` 中的配置文件系统。
- WispOut：带响应格式的 `wispout.json`。
- Event Visor：带 `watchdog` 的事件监视器。
- Speech：语音阅读器。
- 新命令：`append_archivo`、`renombrar_archivo`、`contar_lineas`、`leer_lineas`、`buscar_archivos`、`ejecutar_script`、`listar_habilidades`、`indexar_habilidades`。

### 备注

- 过渡版本。未作为稳定版发布。

---

## [v3.0 整合] - 2026-06-12

第一个被认为可以发布的版本。专注于修复 v2.5 的错误和安全问题，以及添加 `escucha_output`。

### 新增

- `escucha_output.py`：带 5 秒超时的结果编译器。
- `mensaje` 命令。
- `.waio/prompt.txt` 中的可编辑提示词。
- `ver_estado.bat` 和 `limpiar_waio.bat`。
- 编号上下文菜单（4 个条目）。
- JSON 中的 `waio_version` 字段。

### 变更

- 引擎重命名：`waio_escucha_v2.py` -> `waio_escucha.py`。
- 引擎不再写入剪贴板。
- 查看器：标题修复。
- 添加 LICENSE、requirements.txt。

---

## [v2.5 流畅] - 2026-06-12

专注于流畅性的版本：无摩擦输入、更大的读取、安全删除和 Unicode 剪贴板。

### 新增

- TRANSCLIP（`transclip.py`）。
- `trash/` 文件夹。
- 使用 `ctypes` UTF-16 的真实 Unicode 剪贴板。
- 原子 JSON 写入。

### 变更

- `MAX_READ_DEFAULT`：从 100k 到 500k。
- 删除命令：到回收站或 `trash/`。

---

## [v2.0 愿景] - 2026-05-31

第一个可发布版本。相对于之前的 proto-MCP 的概念飞跃。

### 新增

- 带 11 个命令的主引擎。
- `output/` 中的 JSON 反馈。
- 自动剪贴板复制。
- Tkinter 查看器。
- 外科手术式终止开关。
- 安装程序、卸载程序和上下文菜单。

---

## [未发布] - proto-MCP

之前没有自身身份的版本。只有 4 个命令。仅通过日志输出。不保留完整代码。