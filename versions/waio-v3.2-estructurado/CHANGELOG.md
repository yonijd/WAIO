# CHANGELOG - WAIO

Todos los cambios notables de WAIO se documentan en este archivo.

El formato se basa en [Keep a Changelog](https://keepachangelog.com/es/1.0.0/).

---

## [v3.2 Estructurado] - 2026-09-04

Version de reorganizacion completa. El proyecto pasa de tener todo desparramado a tener todo en carpetas. Los comandos dejan de estar en codigo y pasan a ser datos.

### Agregado

- **Estructura de carpetas**: `config/`, `core/`, `data/`, `rescue_tools/`, `skills/`, `temp/`.
- **Comandos base en `core/`**: cada comando es una carpeta con su JSON. Antes estaban hardcodeados en `waio_escucha.py`.
- **`core/indexar/indexar.py`**: indexador independiente que escanea `core/` y `skills/` y genera `data/skills.json`.
- **Comando `skills`**: reemplaza a `listar_habilidades`.
- **Comando `indexar`**: reemplaza a `indexar_habilidades`.
- **Comando `ejecutar`**: reemplaza a `ejecutar_script`. Busca scripts en `skills.json`, `core/`, `skills/` y workdir.
- **Comando `ayuda`**: ayuda general con lista de comandos y perfiles.
- **`config/waio_config.json`**: los 4 perfiles de seguridad.
- **`config/wispout.json`**: formato de respuestas.
- **`config/prompt.txt`**: prompt maestro editable.
- **`data/skills.json`**: catalogo unificado generado por el indexador.
- **`rescue_tools/`**: carpeta con `kill_waio.py`, `stop_monitor.py` y los `.bat` de control.
- **`temp/`**: carpeta unificada para `output/`, `logs/`, `jsonout/`, `workdir.txt`, `waio.lock`.
- **`LICENSE`**: licencia MIT.
- **`requirements.txt`**: `send2trash`, `watchdog`.
- **`.gitignore`**: exclusiones para Python, logs, locks, triggers, backups.

### Cambiado

- **Instalador**: ahora copia carpetas enteras (`CARPETAS_A_COPIAR = ["core", "skills", "rescue_tools", "config", "data", "temp", "trash"]`) en lugar de archivos sueltos.
- **Instalador**: `kill_waio.py` se registra apuntando a `rescue_tools/kill_waio.py` (antes apuntaba a la raiz, donde ya no esta).
- **`waio_escucha.py`**: lee `config/prompt.txt`, `config/waio_config.json`, `data/skills.json`, `config/wispout.json` (antes leia de la raiz).
- **`escucha_output.py`**: lee `config/wispout.json` y escribe en `temp/output/`, `temp/logs/`.
- **`event_visor.py`**: lee `config/wispout.json` y escribe en `temp/logs/`.
- **`transclip.py`**: escribe logs en `temp/logs/`.
- **Menu contextual**: 5 entradas numeradas (`01 Iniciar WAIO`, `02 Visor`, `03 Transclip`, `04 Clip Output`, `05 Kill WAIO`).
- **Skills**: la lista se redujo a las 26 funcionales y auditadas.

### Corregido

- **`kill_waio.py` mal ubicado**: estaba en la raiz pero el instalador lo busca en `rescue_tools/`. Corregido en el instalador.

### Notas

- Bugs conocidos: ver `REPORTE.md`.
- Pendientes:
  - `transclip.py` sigue diciendo `VERSION = "v2.6"`.
  - `total_acciones` no se setea desde el motor.
  - Race condition del `STOP.trigger` (heredada de v2.0).
  - `event_visor` instala `watchdog` automaticamente al arrancar.

---

## [v3.1 Habilidoso] - 2026-07-29

Version de transicion. Introduce sistema de habilidades, perfiles de seguridad configurables, WispOut y dos modulos auxiliares (`event_visor`, `speech`) que no llegaron a consolidarse.

### Agregado

- **Sistema de habilidades**: cada comando es una skill en `habilidades/` (JSON + `.py` opcional).
- **Sistema de perfiles**: `waio_config.json` con 4 perfiles.
- **WispOut**: `wispout.json` con formato de respuestas.
- **Event Visor**: monitor de eventos con `watchdog`.
- **Speech**: lector por voz con `System.Speech.Synthesis`.
- **Comandos nuevos**: `append_archivo`, `renombrar_archivo`, `contar_lineas`, `leer_lineas`, `buscar_archivos`, `ejecutar_script`, `listar_habilidades`, `indexar_habilidades`.
- **Boton PROJECT en el visor**: abre el `WORK_DIR`.
- **Boton EVENTS en el visor**: controla `event_visor`.
- **Sonido de confirmacion** en `escucha_output.py`.
- **Entrada `02 Visor WAIO`** en el menu contextual.

### Cambiado

- **Motor mucho mas grande**: de 28 KB a 65 KB.
- **Visor**: botones en ingles, 9 botones.
- **`ruta_segura`**: respeta el perfil.
- **`eliminar_seguro`**: respeta el modo del perfil.

### Notas

- Version de transicion. No se publico como estable.

---

## [v3.0 Consolidado] - 2026-06-12

Primera version que se considero lista para publicar. Foco en corregir bugs y problemas de seguridad de v2.5, y en agregar `escucha_output`.

### Agregado

- **`escucha_output.py`**: compilador de resultados con timeout de 5s.
- **Comando `mensaje`**.
- **Prompt editable en `.waio/prompt.txt`**.
- **`ver_estado.bat`** y **`limpiar_waio.bat`**.
- **Menu contextual numerado**: 4 entradas.
- **Campo `waio_version`** en los JSONs.

### Cambiado

- **Motor renombrado**: `waio_escucha_v2.py` → `waio_escucha.py`.
- **Motor ya no escribe al portapapeles**.
- **Visor**: titulo corregido.
- **`LICENSE`**, **`requirements.txt`** agregados.

### Corregido

- **Titulo del visor desactualizado**.
- **Saturacion del portapapeles**.
- **Prompt embebido en codigo**.

---

## [v2.5 Fluido] - 2026-06-12

Version centrada en fluidez: entrada sin friccion, lecturas mas grandes, borrado seguro y portapapeles Unicode.

### Agregado

- **TRANSCLIP (`transclip.py`)**.
- **Carpeta `trash/`**.
- **Portapapeles Unicode real** con `ctypes` UTF-16.
- **Escritura atomica de JSON**.

### Cambiado

- **`MAX_READ_DEFAULT`**: de 100k a 500k.
- **Comandos de eliminacion**: a Papelera o `trash/`.
- **`ruta_segura`**: rechaza rutas absolutas antes de resolver.

### Corregido

- **Portapapeles roto con Unicode**.
- **Borrado irreversible**.
- **JSONs corruptos**.

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

### Cambiado

- **Rebranding**: `MCP_ESCUCHA` → `WAIO`.

---

## [No publicado] - proto-MCP

Version previa sin identidad propia. Solo 4 comandos. Salida unicamente por log. No se conserva codigo completo.
