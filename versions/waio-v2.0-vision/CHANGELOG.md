# CHANGELOG - WAIO

Todos los cambios notables de WAIO se documentan en este archivo.

El formato se basa en [Keep a Changelog](https://keepachangelog.com/es/1.0.0/).

---

## [v2.0 Vision] - 2026-10-12

Primera version publicable del proyecto. Salto conceptual respecto al proto-MCP previo no conservado.

### Agregado

- **Motor principal (`waio_escucha_v2.py`)**: 11 comandos (antes 4).
  - Escritura: `crear_archivo`, `crear_carpeta`, `eliminar_archivo`, `eliminar_carpeta`, `mover_archivo`, `copiar_archivo`.
  - Lectura: `listar_directorio`, `leer_archivo`, `existe_archivo`, `obtener_tamano`, `fecha_modificacion`.
- **Multiples alias por comando** (ingles, espanol, shell).
- **Retroalimentacion JSON**: los comandos de lectura generan un JSON en `output/` con el resultado.
- **Copia automatica al portapapeles** de cada resultado.
- **Confirmacion opcional en escrituras** mediante `confirmar: true`.
- **Limite de lectura configurable**: 100k por defecto, hasta 10MB con `limite: 0`.
- **Argumento `--cwd`** para establecer el directorio de trabajo desde el menu contextual.
- **Visor Tkinter (`waio_visor.py`)**: monitoreo en tiempo real de los resultados, con botones de limpiar, copiar, abrir output y limpiar output.
- **Kill switch quirurgico (`kill_waio.py`)**: crea `STOP.trigger` sin matar procesos a lo bruto.
- **Instalador (`instalador_waio.py` + `instalar_waio.bat`)**: copia a `%USERPROFILE%\.waio\` y registra el menu contextual de Windows.
- **Desinstalador (`desinstalador_waio.py` + `desinstalar_waio.bat`)**: limpia archivos y registro.
- **Menu contextual de Windows**: dos entradas (`Iniciar WAIO Aqui`, `Matar WAIO (solo motor)`) en `Directory\shell` y `Directory\Background\shell`.
- **Deteccion multiple de la carpeta Downloads**: UserProfile, Descargas, registro de Windows.
- **Prompt maestro** embebido en el motor y tambien como archivo aparte (`promt maestro.txt`).

### Cambiado

- **Rebranding**: `MCP_ESCUCHA` pasa a llamarse `WAIO` (Web AI Orchestrator).
- **Carpeta de procesados**: `procesados/` pasa a llamarse `jsonout/`.
- **Logs**: pasan a `logs/` con timestamp en el nombre.
- **Rutas seguras**: ahora relativas a `WORK_DIR` en lugar de al directorio del script.

### Corregido

- La carpeta Downloads ya no se asume en `C:\Users\<user>\Downloads`; se detecta en multiples ubicaciones.
- El log ya no se sobrescribe entre ejecuciones (timestamp en el nombre).
- Los logs usan `encoding="ascii", errors="replace"` para evitar problemas de codepage en Windows.
- Se elimino la condicion que ignoraba payloads con el mismo nombre que el anterior.

### Notas

- Existe un proto-MCP previo (no conservado) del cual solo quedan fragmentos y un informe retrospectivo. No se publica como version.
- Bugs conocidos y limitaciones: ver `REPORTE.md`.

---

## [No publicado] - proto-MCP

Version previa sin identidad propia. Solo 4 comandos (`crear_archivo`, `crear_carpeta`, `listar_directorio`, `leer_archivo`). Salida unicamente por log. No se conserva codigo completo.
