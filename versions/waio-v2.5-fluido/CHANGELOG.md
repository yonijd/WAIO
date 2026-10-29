# CHANGELOG - WAIO

Todos los cambios notables de WAIO se documentan en este archivo.

El formato se basa en [Keep a Changelog](https://keepachangelog.com/es/1.0.0/).

---

## [v2.5 Fluido] - 2026-06-12

Version centrada en fluidez: entrada sin friccion, lecturas mas grandes, borrado seguro y portapapeles Unicode real.

### Agregado

- **TRANSCLIP (`transclip.py`)**: puente de portapapeles que traduce comandos simples al formato WAIO. Monitorea el portapapeles cada 500 ms y procesa tres casos: JSON WAIO completo (pasa directo), JSON con solo `comando` (lo envuelve), JSON externo (lo guarda en `externos/`).
- **`iniciar_transclip.bat`**: lanzador de TRANSCLIP con consola titulada "TRADUCTOR WAIO".
- **`detener_escucha.bat`**: detiene TRANSCLIP matando por titulo de ventana, sin tocar otros procesos python.
- **Boton TRANSCLIP en el visor**: toggle INICIAR/CERRAR TRANSCLIP integrado en `waio_visor.py`.
- **Entrada TRANSCLIP en el menu contextual**: tercera opcion bajo WAIO - Web AI Orchestrator.
- **Carpeta `trash/`**: papelera manual cuando `send2trash` no esta instalado.
- **Archivo `transclip.lock`**: bloqueo por PID para evitar instancias duplicadas de TRANSCLIP.
- **Archivo `TRANSCLIP_STOP.trigger`**: senal de parada especifica para TRANSCLIP.
- **Portapapeles Unicode real**: el motor usa `ctypes` con UTF-16 nativo para copiar resultados, con fallback a `clip`.
- **Escritura atomica de JSON**: los resultados se escriben primero a `.tmp` y luego se renombran.
- **Log del motor en UTF-8 puro**: ya no usa `ascii` con `errors="replace"`.

### Cambiado

- **`MAX_READ_DEFAULT`**: de 100,000 a 500,000 caracteres (5x mas).
- **Comandos de eliminacion**: ahora van a la Papelera de Reciclaje (via `send2trash`) o a `trash/` manual. Ya no hay borrado directo.
- **`ruta_segura`**: rechaza explicitamente rutas absolutas antes de resolverlas.
- **`obtener_json_mas_nuevo`**: usa `os.scandir` en lugar de `glob` (mas rapido).
- **Prompt maestro reescrito**: mas corto, con reglas explicitas sobre `transaccion_id` y caracteres de control. Renombrado a `PROMPT_WAIO.txt` (sin typo, sin espacio).
- **Visor**: ventana ampliada de 800x600 a 950x600. Al cerrar, tambien cierra TRANSCLIP.
- **Instalador**: `FILES_TO_COPY` incluye `transclip.py`. Crea `trash/` junto a `logs/`, `output/`, `jsonout/`.
- **Desinstalador**: borra tambien la entrada `transclip` del registro. Los errores ahora se imprimen en lugar de silenciarse.
- **Prompt maestro**: ya no se duplica como archivo aparte con typo. Solo existe `PROMPT_WAIO.txt`.

### Corregido

- **Portapapeles roto con Unicode**: el comando `clip` no manejaba bien tildes ni caracteres especiales. Ahora se usa `ctypes` UTF-16 con fallback.
- **Borrado irreversible**: `eliminar_archivo` y `eliminar_carpeta` ya no borran directo. Envian a Papelera o a `trash/`.
- **JSONs corruptos por muerte a mitad de escritura**: resuelto con escritura atomica (`.tmp` + `rename`).
- **Filtro redundante en `limpiar_output` del visor**: el chequeo sobre `.json` que nunca contenia `PROMPT_WAIO.txt` fue eliminado.

### Notas

- Bugs conocidos y limitaciones: ver `REPORTE.md`.
- El titulo de la ventana del visor sigue diciendo "WAIO VISOR V1.0" (pendiente cosmetico).
- La race condition del `STOP.trigger` en la sustitucion de motor sigue presente (ver REPORTE, seccion de bugs conocidos).

---

## [v2.0 Vision] - 2026-05-31

Primera version publicable del proyecto. Salto conceptual respecto al proto-MCP previo no conservado.

### Agregado

- Motor principal (`waio_escucha_v2.py`) con 11 comandos y multiples alias.
- Retroalimentacion JSON: los comandos de lectura generan un JSON en `output/`.
- Copia automatica al portapapeles de cada resultado.
- Confirmacion opcional en escrituras mediante `confirmar: true`.
- Limite de lectura configurable (100k default, 10MB max).
- Argumento `--cwd` para establecer el directorio de trabajo.
- Visor Tkinter (`waio_visor.py`).
- Kill switch quirurgico (`kill_waio.py`).
- Instalador, desinstalador y menu contextual de Windows.
- Deteccion multiple de la carpeta Downloads.
- Prompt maestro embebido y como archivo aparte.

### Cambiado

- **Rebranding**: `MCP_ESCUCHA` pasa a llamarse `WAIO` (Web AI Orchestrator).
- Carpeta de procesados: `procesados/` pasa a llamarse `jsonout/`.
- Logs pasan a `logs/` con timestamp en el nombre.
- Rutas seguras relativas a `WORK_DIR` en lugar del directorio del script.

---

## [No publicado] - proto-MCP

Version previa sin identidad propia. Solo 4 comandos (`crear_archivo`, `crear_carpeta`, `listar_directorio`, `leer_archivo`). Salida unicamente por log. No se conserva codigo completo.
