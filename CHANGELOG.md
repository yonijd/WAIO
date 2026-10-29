# CHANGELOG - WAIO

Todos los cambios notables de WAIO se documentan en este archivo.

El formato se basa en [Keep a Changelog](https://keepachangelog.com/es/1.0.0/).

---

## [v3.3 Deliberado] - 2026-10-17

Refactor profundo del motor, los satelites, la configuracion y el sistema de respuestas. Cada decision esta tomada conscientemente. Nada es accidental.

### Agregado

- **Formato de respuesta `[SECCION]`**: reemplaza el formato plano. Secciones `[STATUS]`, `[COMANDO]`, `[RESULTADO]`, `[AVISO]`, `[SUSURRO]`, `[RECORDATORIO]`.
- **Timeout configurable en 3 niveles**: accion -> skill -> config. Con tope maximo. Antes era 60s fijo.
- **`WAIO_WORKDIR` por variable de entorno**: el motor se lo pasa a las skills. Corrige el bug de `obtener_workdir` en 22 skills.
- **Orden de procesamiento por `mtime` ascendente**: procesa el JSON mas viejo primero.
- **Cache por `mtime`** en config, skills y wispout. Log limpio.
- **Seguridad implementada de verdad**: limites de lectura/escritura aplicados, validacion de `destino` y `ruta_script`, `carpetas_prohibidas` normalizadas, deteccion de `perfil_activo` invalido.
- **Limites de sistema**: maximo de acciones por transaccion, maximo de transacciones por minuto, maximo de archivos en `output/` y `jsonout/`.
- **Estructura `core/`**: los comandos base y scripts principales se movieron a `core/` (uno por carpeta). Se agrego `core/voz`, `core/listia`, `core/ejecutar_comando`, etc.
- **Doble hilo (Watcher + Procesador)**: el motor ahora tiene un hilo que escanea `Downloads/` y mueve a `temp/queue/`, y otro que procesa la cola. Evita cuelgues.
- **Recuperacion de crashes**: si el motor se cierra a mitad de una transaccion, al arrancar mueve los JSON de `temp/processing/` a `temp/jsonout/rechazados/` con un `.error.txt`.
- **Indice de duplicados**: el motor rechaza `transaccion_id` que ya fueron procesados (configurable).
- **Lista negra de nombres reservados**: bloquea `CON`, `NUL`, `PRN`, `AUX`, `COM1-9`, `LPT1-9` y el caracter `:`.
- **Sanitizacion de `transaccion_id`**: valida y reemplaza caracteres invalidos antes de usarlo en nombres de archivo.
- **`ejecutar_comando` como comando nativo**: solo disponible en perfil `debug`, con whitelist de comandos, bloqueo de `python -c`, `python -m`, pipes y redirecciones.
- **18 campos nuevos** en `waio_config.json` (incluyendo `directorio_escucha`, `leer_json_en_downloads`, `aceptar_id_duplicado`).
- **`rescue_tools/` consolidado**: `kill_waio.py`, `limpiar_waio.py`, `ver_estado.py`, desinstalador, `README.md`.
- **Botones `CONF`, `WISP` y `PROMPT`** en el visor.
- **`total_acciones`** seteado desde el motor (corrige el bug de v3.2).
- **`pid_es_python`**: antes de matar el PID del lock, verifica con `tasklist` que sea Python.

### Cambiado

- **Motor mucho mas grande**: de 65 KB a 74 KB. Incluye cache, timeouts, limites y seguridad.
- **`escucha_output.py`**: fix del `GlobalLock fallo` usando `ctypes` con timeout de 3s. Buffer ordenado por `(transaccion_id, accion_idx)`.
- **`waio_visor.py`**: copia al portapapeles eliminada de `mostrar_json`. Botones `CONF`, `WISP` y `PROMPT`. Mensajes en ingles. Lee `visor_max_lines` y `visor_refresh_ms` del config.
- **Instalador**: NO copia `temp/` (arrastra logs y basura). NO copia `trash/` (el motor la crea). Crea `temp/` vacia. `limpiar_entradas_viejas` borra claves obsoletas. `validar_src_dir` verifica que no se instale sobre si mismo.
- **Desinstalador**: `borrar_clave_recursiva` para borrar claves con subclaves. Preserva `trash/` y `temp/logs/` si el usuario lo pide.
- **Menu contextual**: 4 entradas (se saco `04_clip_output`, `05_kill_waio` paso a `04_kill_waio`).
- **`wispout.json`**: estructura completamente nueva. Cada seccion tiene reglas (`activo`, `inicio_accion`, `duracion_acciones`, `cada_cuantas_acciones`, `repeticion_cada`, `mostrar_en_error`, `mostrar_en_primera`).
- **Perfiles renombrados**: `solo_lectura` -> `readonly`, `estandar` -> `standard`, `avanzado` -> `advanced`, `sin_restricciones` -> `debug`. Se agrego `permite_ejecutar_core/skills/workdir/disco`.
- **`limite_lectura_bytes`** renombrado a **`limite_lectura_chars`**.

### Corregido

- **`GlobalLock fallo`** en `copiar_portapapeles` (era un bug de handles de 64 bits).
- **`total_acciones`** no seteado desde el motor.
- **Cache de alias**: ahora el mapeo se reconstruye con `construir_mapeo_comandos()`.
- **`obtener_workdir`** en 22 skills.
- **Colision de alias**: `grep` removido de `buscar_contenido`, `info` removido de `skills`.
- **Seguridad de `ejecutar_comando`**: `shell=True` removido, `python -c` y `python -m` bloqueados, pipes y redirecciones bloqueadas, whitelist de comandos.

### Notas

- Bugs conocidos: ver `REPORTE.md`.
- Pendientes:
  - GUIs de config y wispout (botones preparados, sin codigo).
  - `event_visor.py` sin auditar.
  - Rotacion de logs (`logs_retention_days: 7` en config pero no se aplica).

---

## [v3.2 Estructurado] - 2026-09-04

Version de reorganizacion completa. El proyecto pasa de tener todo desparramado a tener todo en carpetas. Los comandos dejan de estar en codigo y pasan a ser datos.

### Agregado

- **Estructura de carpetas**: `config/`, `core/`, `data/`, `rescue_tools/`, `skills/`, `temp/`.
- **Comandos base en `core/`**: cada comando es una carpeta con su JSON.
- **`core/indexar/indexar.py`**: indexador independiente.
- **Comandos unificados**: `skills`, `indexar`, `ejecutar`, `ayuda`.
- **`rescue_tools/`**: kill_waio, stop_monitor, bats.
- **`LICENSE`**, **`requirements.txt`**, **`.gitignore`**.

### Cambiado

- **Instalador**: copia carpetas enteras en lugar de archivos sueltos.
- **Motor**: lee de `config/`, `data/`, `temp/`.

---

## [v3.1 Habilidoso] - 2026-07-29

Version de transicion. Introduce sistema de habilidades, perfiles de seguridad configurables, WispOut y dos modulos auxiliares (`event_visor`, `speech`) que no llegaron a consolidarse.

### Agregado

- Sistema de habilidades en `habilidades/`.
- Sistema de perfiles en `waio_config.json`.
- WispOut: `wispout.json` con formato de respuestas.
- Event Visor: monitor de eventos con `watchdog`.
- Speech: lector por voz.
- Comandos nuevos: `append_archivo`, `renombrar_archivo`, `contar_lineas`, `leer_lineas`, `buscar_archivos`, `ejecutar_script`, `listar_habilidades`, `indexar_habilidades`.

### Notas

- Version de transicion. No se publico como estable.

---

## [v3.0 Consolidado] - 2026-06-12

Primera version que se considero lista para publicar. Foco en corregir bugs y problemas de seguridad de v2.5, y en agregar `escucha_output`.

### Agregado

- `escucha_output.py`: compilador de resultados con timeout de 5s.
- Comando `mensaje`.
- Prompt editable en `.waio/prompt.txt`.
- `ver_estado.bat` y `limpiar_waio.bat`.
- Menu contextual numerado (4 entradas).
- Campo `waio_version` en los JSONs.

### Cambiado

- Motor renombrado: `waio_escucha_v2.py` -> `waio_escucha.py`.
- Motor ya no escribe al portapapeles.
- Visor: titulo corregido.
- LICENSE, requirements.txt agregados.

---

## [v2.5 Fluido] - 2026-06-12

Version centrada en fluidez: entrada sin friccion, lecturas mas grandes, borrado seguro y portapapeles Unicode.

### Agregado

- TRANSCLIP (`transclip.py`).
- Carpeta `trash/`.
- Portapapeles Unicode real con `ctypes` UTF-16.
- Escritura atomica de JSON.

### Cambiado

- `MAX_READ_DEFAULT`: de 100k a 500k.
- Comandos de eliminacion: a Papelera o `trash/`.

---

## [v2.0 Vision] - 2026-05-31

Primera version publicable. Salto conceptual respecto al proto-MCP previo.

### Agregado

- Motor principal con 11 comandos.
- Retroalimentacion JSON en `output/`.
- Copia automatica al portapapeles.
- Visor Tkinter.
- Kill switch quirurgico.
- Instalador, desinstalador y menu contextual.

---

## [No publicado] - proto-MCP

Version previa sin identidad propia. Solo 4 comandos. Salida unicamente por log. No se conserva codigo completo.
