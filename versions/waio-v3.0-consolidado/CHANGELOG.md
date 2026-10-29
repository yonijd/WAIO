# CHANGELOG - WAIO

Todos los cambios notables de WAIO se documentan en este archivo.

El formato se basa en [Keep a Changelog](https://keepachangelog.com/es/1.0.0/).

---

## [v3.0 Consolidado] - 2026-06-12

Primera version que se considero lista para publicar. Foco en corregir bugs y problemas de seguridad de v2.5, y en agregar `escucha_output`.

### Agregado

- **`escucha_output.py`**: compilador de resultados. Monitorea `output/`, acumula JSONs en un buffer y, tras 5 segundos sin novedades, los copia al portapapeles como un unico bloque con contexto (`[N] TX: xxx | Accion X/Y | Comando: xxx`).
- **Comando `mensaje`**: permite a la IA comunicarse directamente sin tocar el sistema de archivos. Total de comandos: 12.
- **Prompt editable en `.waio/prompt.txt`**: el prompt ya no vive en el codigo. El motor lo crea con un valor por defecto si no existe y lo procesa en cada arranque.
- **`ver_estado.bat`**: herramienta de diagnostico (procesos, locks, triggers, archivos clave). Guarda log en `logs/estado_*.log`.
- **`limpiar_waio.bat`**: mata todos los procesos WAIO y borra triggers/locks huerfanos.
- **`iniciar_escucha_output.bat`** y **`detener_escucha_output.bat`**: lanzador y detenedor de escucha_output.
- **`iniciar_transclip.bat`** y **`detener_transclip.bat`**: reemplazan a los de v2.5 con nombres mas consistentes.
- **Boton ESCUCHA OUTPUT en el visor**: toggle INICIAR/CERRAR.
- **Inicio automatico de escucha_output**: el visor lo lanza al abrirse.
- **Menu contextual numerado**: 4 entradas con prefijo `01_`, `02_`, `03_`, `04_` para forzar orden fijo.
- **Campo `waio_version` en los JSON de resultado**: cada resultado ahora indica la version que lo genero.

### Cambiado

- **Motor renombrado**: `waio_escucha_v2.py` pasa a `waio_escucha.py`. Se elimina el sufijo `_v2`.
- **Motor ya no escribe al portapapeles**: esa responsabilidad paso integramente a `escucha_output.py`.
- **Visor**: titulo corregido a `WAIO VISOR 3.0` (antes decia `WAIO VISOR V1.0` desde v2.0). Ventana sigue en 950x600. Botones reordenados a 6.
- **Instalador**: `FILES_TO_COPY` crece de 4 a 12 archivos. Ahora copia tambien `escucha_output.py`, `desinstalador_waio.py`, `desinstalar_waio.bat`, los 4 `.bat` de inicio/detencion y `ver_estado.bat`.
- **Desinstalador**: borra las 4 entradas numeradas del menu contextual.
- **Menu contextual**: pasa de 3 entradas sin numerar a 4 entradas numeradas.
- **Prompt maestro**: reescrito para v3, mas conciso, con mencion a `escucha_output` y al comando `mensaje`.
- **`.gitignore`**: se incorpora por primera vez en esta version.
- **`LICENSE`**: se incorpora licencia MIT.
- **`requirements.txt`**: declara `send2trash>=1.8.0` como unica dependencia externa.

### Corregido

- **Titulo del visor desactualizado**: de `WAIO VISOR V1.0` a `WAIO VISOR 3.0`.
- **Saturacion del portapapeles**: en v2.5 cada comando copiaba su resultado por separado. Ahora escucha_output los agrupa y da contexto.
- **Prompt embebido en codigo**: ya no hay que tocar Python para ajustar las reglas de la IA.
- **Menu contextual desordenado**: el orden alfabetico aleatorio se reemplazo por prefijos numericos.
- **Falta de herramientas de diagnostico**: se agregaron `ver_estado.bat` y `limpiar_waio.bat`.

### Notas

- Bugs conocidos y limitaciones: ver `REPORTE.md`.
- Bugs pendientes (documentados, no corregidos en esta version):
  - El campo `total_acciones` no se setea desde el motor, por lo que escucha_output cae al formato sin total.
  - `transclip.py` mantiene `VERSION = "v2.5"` aunque forme parte de v3.
  - `iniciar_escucha_output.bat` tiene errores tipograficos (`chcp 65001 nul` y `timeout t 2 nobreak nul`).
  - Race condition del `STOP.trigger` en la sustitucion de motor (heredada de v2.0).
- Existe un proto-MCP previo (no conservado) del cual solo quedan fragmentos.

---

## [v2.5 Fluido] - 2026-06-12

Version centrada en fluidez: entrada sin friccion, lecturas mas grandes, borrado seguro y portapapeles Unicode real.

### Agregado

- **TRANSCLIP (`transclip.py`)**: puente de portapapeles que traduce comandos simples al formato WAIO.
- **`iniciar_transclip.bat`** y **`detener_escucha.bat`**: lanzador y detenedor.
- **Boton TRANSCLIP en el visor**: toggle INICIAR/CERRAR.
- **Carpeta `trash/`**: papelera manual cuando `send2trash` no esta instalado.
- **Archivo `transclip.lock`**: bloqueo por PID para evitar instancias duplicadas.
- **Archivo `TRANSCLIP_STOP.trigger`**: senal de parada de TRANSCLIP.
- **Portapapeles Unicode real**: el motor usa `ctypes` con UTF-16 nativo, con fallback a `clip`.
- **Escritura atomica de JSON**: los resultados se escriben primero a `.tmp` y luego se renombran.

### Cambiado

- **`MAX_READ_DEFAULT`**: de 100,000 a 500,000 caracteres.
- **Comandos de eliminacion**: van a la Papelera de Reciclaje (via `send2trash`) o a `trash/` manual.
- **`ruta_segura`**: rechaza explicitamente rutas absolutas antes de resolverlas.
- **`obtener_json_mas_nuevo`**: usa `os.scandir` en lugar de `glob`.
- **Prompt maestro reescrito y renombrado** a `PROMPT_WAIO.txt`.
- **Visor**: ventana de 800x600 a 950x600.
- **Instalador**: incluye `transclip.py`. Crea `trash/`.
- **Desinstalador**: borra tambien la entrada `transclip`.

### Corregido

- **Portapapeles roto con Unicode**: `clip` no manejaba tildes. Ahora `ctypes` UTF-16.
- **Borrado irreversible**: `eliminar_archivo` y `eliminar_carpeta` ya no borran directo.
- **JSONs corruptos por muerte a mitad de escritura**: escritura atomica.
- **Filtro redundante en `limpiar_output` del visor**: eliminado.

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
- Rutas seguras relativas a `WORK_DIR`.

---

## [No publicado] - proto-MCP

Version previa sin identidad propia. Solo 4 comandos (`crear_archivo`, `crear_carpeta`, `listar_directorio`, `leer_archivo`). Salida unicamente por log. No se conserva codigo completo.
