# CHANGELOG - WAIO

Todos los cambios notables de WAIO se documentan en este archivo.

El formato se basa en [Keep a Changelog](https://keepachangelog.com/es/1.0.0/).

---

## [v3.1 Habilidoso] - 2026-07-29

Version de transicion con cambio de paradigma. Introduce sistema de habilidades, perfiles de seguridad configurables, WispOut y dos modulos auxiliares (event_visor y speech) que no llegaron a consolidarse.

### Agregado

- **Sistema de habilidades**: cada comando es una skill en `habilidades/` (JSON + `.py` opcional). Indexacion automatica al arrancar con validacion de campos obligatorios.
- **Sistema de perfiles de seguridad** (`waio_config.json`): cuatro perfiles (`solo_lectura`, `estandar`, `avanzado`, `sin_restricciones`) con sandbox, rutas absolutas, modo de borrado, limites de escritura y lectura, carpetas prohibidas y permisos de scripts.
- **WispOut** (`wispout.json`): formato de respuestas con encabezado contextual (`WAIO 3.1 | avanzado | 10MB | papelera`), recordatorios, susurros y respuestas especiales.
- **Event Visor** (`event_visor.py`): monitor de eventos del sistema de archivos con `watchdog`. Actualiza el recordatorio de WispOut con eventos recientes. Se controla desde el boton EVENTS del visor.
- **Speech** (`speech.py`): lector por voz con `System.Speech.Synthesis`. Lee el ultimo JSON de `jsonout/`.
- **Stop Event Visor** (`stop_event_visor.py`): detenedor de `event_visor` por PID (bug: busca `event_visor.pid` pero el visor crea `events.lock`).
- **Comandos nuevos**: `append_archivo`, `renombrar_archivo`, `contar_lineas`, `leer_lineas`, `buscar_archivos`, `ejecutar_script`, `listar_habilidades`, `indexar_habilidades`.
- **Boton PROJECT en el visor**: abre el `WORK_DIR` guardado en `workdir.txt`.
- **Boton EVENTS en el visor**: controla `event_visor`.
- **Boton LISTEN en el visor**: reemplaza al boton ESCUCHA OUTPUT de v3.0.
- **Sonido de confirmacion** en `escucha_output.py` al copiar al portapapeles (`SystemAsterisk`).
- **Entrada `02 Visor WAIO`** en el menu contextual (ahora 5 entradas).
- **Carpetas** `pyhabilidades/` y `pyseguras/` para scripts de skills y del usuario.
- **Archivo `workdir.txt`** para que el visor sepa donde abrir PROJECT.

### Cambiado

- **Motor mucho mas grande**: `waio_escucha.py` pasa de 28 KB a 65 KB. Ahora incluye carga de config, indexacion de habilidades, formateo de respuestas y validacion de perfiles.
- **Visor**: botones en ingles y reorganizados. Ahora son 9: CLEAN, OUTPUT, PROJECT, TRANSCLIP, LISTEN, EVENTS, COPY, CLEAN OUTPUT.
- **`ruta_segura`** ahora respeta el perfil: en sandbox rechaza rutas absolutas, en no-sandbox las acepta.
- **`eliminar_seguro`** respeta el modo del perfil: `papelera` usa `send2trash`, `permanente` usa `unlink`/`rmtree` directo.
- **Instalador**: `FILES_TO_COPY` crece a 15 archivos. Nuevos: `waio_config.json`, `wispout.json`, `habilidades.json`.
- **Desinstalador**: actualizado para borrar 5 entradas numeradas en lugar de 4 (corregido en auditoria, el original decia `VERSION = "3.0"`).
- **Menu contextual**: 5 entradas numeradas (`01_` a `05_`).

### Corregido

- (Nada, esta version no corrige bugs de v3.0)

### Notas

- **Version de transicion.** No se publico como estable. Muchos componentes quedaron a medio camino.
- Bugs conocidos: ver `REPORTE.md`. Los mas importantes:
  - El instalador **no copia** `event_visor.py`, `speech.py` ni `stop_event_visor.py` a `.waio/`. El boton EVENTS del visor no funciona en instalaciones reales.
  - `stop_event_visor.py` busca `event_visor.pid` pero `event_visor.py` crea `events.lock`. No funciona.
  - `speech.py` lee el campo `contenido` pero la mayoria de los JSONs tienen `output`. Solo funciona con el comando `mensaje`.
  - `limpiar_waio.bat` no limpia `events.lock` ni `EVENTS_STOP.trigger`.
  - `ver_estado.bat` no reporta el estado de `event_visor`.
  - Typos heredados en `iniciar_escucha_output.bat`.
  - Race condition del `STOP.trigger` (heredada de v2.0).
  - `total_acciones` no seteado desde el motor (heredado de v3.0).
- `event_visor` resulto poco util y desaparece en versiones posteriores.

---

## [v3.0 Consolidado] - 2026-06-12

Primera version que se considero lista para publicar. Foco en corregir bugs y problemas de seguridad de v2.5, y en agregar `escucha_output`.

### Agregado

- **`escucha_output.py`**: compilador de resultados. Monitorea `output/`, acumula JSONs en un buffer y, tras 5 segundos, los copia al portapapeles como un unico bloque con contexto.
- **Comando `mensaje`**: comunicacion directa sin tocar el sistema de archivos.
- **Prompt editable en `.waio/prompt.txt`**: el prompt ya no vive en el codigo.
- **`ver_estado.bat`**: herramienta de diagnostico.
- **`limpiar_waio.bat`**: limpieza de procesos y triggers.
- **`iniciar_escucha_output.bat`** y **`detener_escucha_output.bat`**.
- **`iniciar_transclip.bat`** y **`detener_transclip.bat`**.
- **Boton ESCUCHA OUTPUT en el visor**.
- **Inicio automatico de escucha_output** al abrir el visor.
- **Menu contextual numerado**: 4 entradas (`01_` a `04_`).
- **Campo `waio_version`** en los JSONs de resultado.

### Cambiado

- **Motor renombrado**: `waio_escucha_v2.py` pasa a `waio_escucha.py`.
- **Motor ya no escribe al portapapeles**: delegado a `escucha_output.py`.
- **Visor**: titulo corregido a `WAIO VISOR 3.0`.
- **Instalador**: `FILES_TO_COPY` crece de 4 a 12 archivos.
- **Desinstalador**: borra las 4 entradas numeradas.
- **Menu contextual**: 4 entradas numeradas.
- **Prompt maestro**: reescrito, mas conciso.
- **`.gitignore`**, **`LICENSE`** (MIT) y **`requirements.txt`** agregados.

### Corregido

- **Titulo del visor desactualizado**: de `WAIO VISOR V1.0` a `WAIO VISOR 3.0`.
- **Saturacion del portapapeles**: ahora `escucha_output` agrupa resultados.
- **Prompt embebido en codigo**: ahora editable.
- **Menu contextual desordenado**: prefijos numericos.
- **Falta de herramientas de diagnostico**: `ver_estado.bat` y `limpiar_waio.bat`.

---

## [v2.5 Fluido] - 2026-06-12

Version centrada en fluidez: entrada sin friccion, lecturas mas grandes, borrado seguro y portapapeles Unicode real.

### Agregado

- **TRANSCLIP (`transclip.py`)**: puente de portapapeles que traduce comandos simples.
- **`iniciar_transclip.bat`** y **`detener_escucha.bat`**.
- **Boton TRANSCLIP en el visor**.
- **Carpeta `trash/`**: papelera manual.
- **Archivo `transclip.lock`**.
- **Archivo `TRANSCLIP_STOP.trigger`**.
- **Portapapeles Unicode real** con `ctypes` UTF-16.
- **Escritura atomica de JSON**.

### Cambiado

- **`MAX_READ_DEFAULT`**: de 100,000 a 500,000 caracteres.
- **Comandos de eliminacion**: a la Papelera o `trash/`.
- **`ruta_segura`**: rechaza rutas absolutas antes de resolverlas.
- **`obtener_json_mas_nuevo`**: usa `os.scandir` en lugar de `glob`.
- **Prompt maestro reescrito y renombrado** a `PROMPT_WAIO.txt`.
- **Visor**: ventana de 800x600 a 950x600.
- **Instalador**: incluye `transclip.py`.
- **Desinstalador**: borra tambien la entrada `transclip`.

### Corregido

- **Portapapeles roto con Unicode**.
- **Borrado irreversible**.
- **JSONs corruptos por muerte a mitad de escritura**.
- **Filtro redundante en `limpiar_output` del visor**.

---

## [v2.0 Vision] - 2026-05-31

Primera version publicable del proyecto. Salto conceptual respecto al proto-MCP previo no conservado.

### Agregado

- Motor principal (`waio_escucha_v2.py`) con 11 comandos y multiples alias.
- Retroalimentacion JSON en `output/`.
- Copia automatica al portapapeles.
- Confirmacion opcional en escrituras.
- Limite de lectura configurable.
- Argumento `--cwd`.
- Visor Tkinter.
- Kill switch quirurgico.
- Instalador, desinstalador y menu contextual.
- Deteccion multiple de Downloads.
- Prompt maestro embebido.

### Cambiado

- **Rebranding**: `MCP_ESCUCHA` pasa a `WAIO`.
- **Carpeta**: `procesados/` pasa a `jsonout/`.
- **Logs**: a `logs/` con timestamp.
- **Rutas seguras**: relativas a `WORK_DIR`.

---

## [No publicado] - proto-MCP

Version previa sin identidad propia. Solo 4 comandos. Salida unicamente por log. No se conserva codigo completo.
