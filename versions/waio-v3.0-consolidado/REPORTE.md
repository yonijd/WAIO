# REPORTE TECNICO - WAIO v3.0 Consolidado

Auditoria tecnica de la version 3.0 Consolidado del motor WAIO (Web AI Orchestrator).

---

## 1. Ficha Tecnica

| Campo | Valor |
|---|---|
| Version | v3.0 Consolidado |
| Fecha de auditoria | 2026-10-12 |
| Archivos totales | 20 (tras limpieza) |
| Tamaño total | ~103 KB |
| Tipos dominantes | .bat (8), .py (7), .txt (2), .md (2) |
| Plataforma objetivo | Windows 10/11 |
| Lenguaje | Python 3.8+ |
| Dependencias externas | `send2trash` opcional |
| Licencia | MIT |

---

## 2. Arquitectura

WAIO v3.0 Consolidado opera con **cuatro procesos coordinados** que se comunican a traves del sistema de archivos. Es la primera version donde el motor delega completamente la comunicacion con el usuario a otro proceso.

### 2.1 Motor (`waio_escucha.py`)
Proceso principal. Escucha la carpeta Downloads en busca de archivos JSON, los valida y ejecuta las acciones que contienen. Es el unico componente con permisos de escritura real sobre el sistema de archivos, siempre confinado al `WORK_DIR`.

**Responsabilidades en v3.0:**
- Detectar y procesar JSONs
- Ejecutar los 12 comandos
- Escribir resultados en `output/`
- Leer/crear el prompt editable en `.waio/prompt.txt`
- **NO** copia al portapapeles (delegado a escucha_output)

### 2.2 Visor (`waio_visor.py`)
Interfaz grafica en Tkinter. Monitorea `output/` y muestra los resultados. Controla el ciclo de vida de TRANSCLIP y escucha_output mediante dos botones toggle. Al cerrarse, apaga todos los procesos hijos.

**Responsabilidades en v3.0:**
- Mostrar resultados
- Lanzar escucha_output automaticamente al abrirse
- Controlar TRANSCLIP y escucha_output
- Coordinar el apagado de todos los procesos

### 2.3 TRANSCLIP (`transclip.py`)
Puente de portapapeles. Monitorea el portapapeles cada 500 ms y traduce comandos simples al formato WAIO. Genera JSONs y los deja en Downloads.

**Sin cambios funcionales respecto a v2.5.**

### 2.4 Escucha Output (`escucha_output.py`) — NUEVO en v3.0
Compilador de resultados. Monitorea `output/` cada 500 ms, acumula JSONs en un buffer y, tras 5 segundos sin novedades, compila un unico bloque con contexto completo y lo copia al portapapeles.

**Responsabilidades:**
- Detectar nuevos JSONs en `output/`
- Acumularlos en buffer (maximo 50 items)
- Compilar con formato `[N] TX: xxx | Accion X/Y | Comando: xxx`
- Copiar al portapapeles con `ctypes` UTF-16 (fallback a `clip`)
- Instancia unica via `escucha.lock`

### Diagrama de flujo

```
[IA web/local]
     |
     | genera JSON (completo o simple)
     v
[Portapapeles]  <--->  [transclip.py]
     |                       |
     |                       | envuelve y guarda
     |                       v
     +--------------> [Downloads/]
                             |
                             | motor detecta (polling cada 2s)
                             v
                    [waio_escucha.py] --- lanza ---> [waio_visor.py]
                             |                              |
                             | ejecuta acciones             | lanza
                             v                              v
                    [WORK_DIR] (confinado)          [escucha_output.py]
                             |                              |
                             | guarda resultados            |
                             v                              |
                        [output/] <------ monitorea ---------+
                             |                              |
                             | archivo procesado            | compila
                             v                              v
                        [jsonout/]                  [Portapapeles]
                                                            |
                                                            v
                                                   Usuario pega a la IA
```

---

## 3. Flujo de Carpetas

WAIO v3.0 Consolidado gestiona **cuatro carpetas** dentro de `%USERPROFILE%\.waio\`, mas una externa:

| Carpeta | Proposito | Creada por |
|---|---|---|
| `logs/` | Logs de motor, visor, TRANSCLIP, escucha_output y ver_estado | Motor + otros |
| `output/` | Resultados JSON de comandos + prompt procesado | Motor |
| `jsonout/` | Payloads JSON ya procesados (historial) | Motor |
| `trash/` | Papelera manual (solo si `send2trash` no esta) | Motor |
| `Downloads/` o `Descargas/` | Carpeta de entrada (fuera de `.waio`) | Sistema |

**Archivos de control en `.waio/`:**

| Archivo | Proposito |
|---|---|
| `prompt.txt` | Prompt editable por el usuario |
| `transclip.lock` | PID de la instancia activa de TRANSCLIP |
| `escucha.lock` | PID de la instancia activa de escucha_output |
| `STOP.trigger` | Senal de parada del motor |
| `TRANSCLIP_STOP.trigger` | Senal de parada de TRANSCLIP |
| `ESCUCHA_STOP.trigger` | Senal de parada de escucha_output |

---

## 4. Evolucion respecto a versiones anteriores

### 4.1 Comparativa v2.5 Fluido -> v3.0 Consolidado

| Area | v2.5 Fluido | v3.0 Consolidado | Tipo |
|---|---|---|---|
| Comandos | 11 | 12 (+`mensaje`) | Nuevo comando |
| Prompt | Embebido en motor | Editable en `.waio/prompt.txt` | Externalizacion |
| Portapapeles | Motor copiaba | `escucha_output.py` compila y copia | Separacion |
| Resultados multiples | Copia individual saturada | Bloque compilado con contexto | Feature nueva |
| Procesos coordinados | 3 (motor, visor, kill) | 4 (+ escucha_output) | Crecimiento |
| Menu contextual | 3 entradas sin numerar | 4 entradas numeradas | Orden fijo |
| Botones visor | 5 | 6 | Reorganizacion |
| Diagnostico | Inexistente | `ver_estado.bat` + `limpiar_waio.bat` | Nuevas herramientas |
| Titulo visor | `WAIO VISOR V1.0` (bug) | `WAIO VISOR 3.0` | Correccion |
| `.gitignore` | No existia | Si | Preparacion para publicar |
| `LICENSE` | No existia | MIT | Preparacion para publicar |
| `requirements.txt` | No existia | `send2trash>=1.8.0` | Documentacion |
| Campo `waio_version` en JSON | No existia | Si | Trazabilidad |

### 4.2 Comparativa ecosistema

| Pieza | v2.5 Fluido | v3.0 Consolidado |
|---|---|---|
| Motor | `waio_escucha_v2.py` (29.02 KB) | `waio_escucha.py` (28.08 KB) |
| Visor | `waio_visor.py` (11.38 KB) | `waio_visor.py` (13.94 KB) |
| TRANSCLIP | `transclip.py` (12.01 KB) | `transclip.py` (12.01 KB, sin cambios) |
| Escucha Output | No existia | `escucha_output.py` (9.21 KB) |
| Kill switch | `kill_waio.py` (299 B) | `kill_waio.py` (299 B, sin cambios) |
| Instalador | 4.96 KB | 4.96 KB |
| Desinstalador | 2.70 KB | 2.86 KB |
| Prompt | `PROMPT_WAIO.txt` (1.58 KB) | `.waio/prompt.txt` (embebido como default) |

### 4.3 Conclusion de la evolucion

v3.0 Consolidado tiene dos ejes claros:

1. **Corregir los bugs y problemas de seguridad de v2.5.** El titulo del visor, el menu contextual desordenado, la falta de herramientas de diagnostico, el prompt embebido en codigo — todo eso se resolvio.
2. **Agregar `escucha_output`.** El compilador de resultados es la unica feature nueva grande, y resuelve el problema de saturacion del portapapeles que arrastraba v2.5.

No hay un cambio conceptual de fondo. La arquitectura sigue siendo la misma. Lo que cambia es la **solidez**: esta version es la primera que se considero lista para publicar.

---

## 5. Diseño de Seguridad

### 5.1 Confinamiento de rutas (`ruta_segura`)

Todas las rutas pasan por `ruta_segura()`, que:
1. Rechaza explicitamente rutas absolutas antes de intentar resolverlas.
2. Convierte rutas relativas a absolutas usando `WORK_DIR` como base.
3. Resuelve symlinks con `.resolve()`.
4. Verifica que la ruta final este dentro de `WORK_DIR` con `.relative_to()`.
5. Si falla, registra el intento en el log y retorna `None`.

### 5.2 Borrado seguro

`eliminar_archivo` y `eliminar_carpeta` usan `eliminar_seguro()`:
1. Intenta `send2trash` (Papelera de Reciclaje nativa).
2. Si no esta instalado, mueve a `trash/` con timestamp en el nombre.

### 5.3 Escritura atomica de JSON

Los resultados se escriben primero a `.tmp` y luego se renombran. Evita JSONs corruptos si el proceso muere entre la apertura y el cierre del archivo.

### 5.4 Portapapeles Unicode real

escucha_output usa `ctypes` para abrir el portapapeles y escribir en UTF-16 nativo. Si falla, cae al `clip` tradicional como respaldo.

### 5.5 Instancia unica

TRANSCLIP y escucha_output usan archivos `.lock` con PID para evitar duplicados. Al arrancar, si el lock existe, verifican si el PID sigue vivo con `tasklist`.

### 5.6 Senales de parada independientes

Hay tres triggers de parada:
- `STOP.trigger`: apaga el motor.
- `TRANSCLIP_STOP.trigger`: apaga TRANSCLIP.
- `ESCUCHA_STOP.trigger`: apaga escucha_output.

Cada proceso verifica su trigger en su bucle. El visor los crea todos al cerrarse, garantizando que no queden procesos huerfanos.

---

## 6. Bugs Conocidos y Race Conditions

### 6.1 Race condition en la sustitucion de motor (heredada de v2.0)

En `main()`, el motor nuevo crea un `STOP.trigger` para matar al motor anterior, espera 1 segundo, y lo elimina. Pero el loop del motor anterior es de 2 segundos. Si el motor anterior esta en medio de un ciclo cuando se crea el STOP, no lo vera hasta el siguiente ciclo, que puede ser hasta 2 segundos despues. Resultado: el STOP se elimina antes de que el motor anterior lo detecte.

**Impacto:** dos motores pueden quedar corriendo simultaneamente. No es critico (ambos son idempotentes), pero no es lo esperado.

**Estado:** documentado, no corregido en v3.0.

### 6.2 Campo `total_acciones` no seteado

`escucha_output.py` busca el campo `total_acciones` en los JSONs para armar el encabezado `[N] TX: xxx | Accion X/Y | Comando: xxx`. Pero el motor (`waio_escucha.py`) **no guarda ese campo** en `guardar_resultado_json`. El propio comentario del codigo lo reconoce: *"Lo agregaremos al motor"*.

**Impacto:** escucha_output cae al formato sin total (`Accion X | Comando: xxx`). Funciona, pero pierde informacion de contexto.

**Estado:** documentado, no corregido en v3.0.

### 6.3 `transclip.py` mantiene `VERSION = "v2.5"`

El archivo `transclip.py` que forma parte de v3.0 Consolidado sigue declarando `VERSION = "v2.5"` internamente. No se actualizo al renombrar la version.

**Impacto:** cosmetico. El titulo de la ventana de TRANSCLIP dice `TRANSCLIP - v2.5`.

**Estado:** documentado, no corregido en v3.0.

### 6.4 Typos en `iniciar_escucha_output.bat`

El archivo tiene dos errores tipograficos:
- `chcp 65001 nul` — falta el `>` antes de `nul`.
- `timeout t 2 nobreak nul` — faltan las barras: deberia ser `timeout /t 2 /nobreak >nul`.

**Impacto:** el `.bat` no ejecuta esas lineas correctamente. La funcionalidad principal (lanzar escucha_output) si funciona.

**Estado:** documentado, no corregido en v3.0.

### 6.5 Alias con caracteres no-ASCII

Los alias `obtener_tamaño` (con ñ) y `fecha_modificación` (con tilde) funcionan en Python 3 con UTF-8, pero pueden dar problemas si el payload JSON se genera con encoding incorrecto.

**Impacto:** bajo. Los alias sin caracteres especiales funcionan siempre.

**Estado:** documentado.

---

## 7. Decisiones de Diseño Notables

### 7.1 El motor ya no toca el portapapeles

En v2.5 el motor copiaba cada resultado al portapapeles. En v3.0 esa responsabilidad paso integramente a `escucha_output.py`. Esto separa dos preocupaciones: **ejecutar** (motor) y **comunicar** (escucha_output). El motor queda mas simple y escucha_output puede especializarse en el formato de salida.

### 7.2 Prompt editable externalizado

El prompt vive en `.waio/prompt.txt`. El motor lo lee al arrancar y lo escribe en `output/` como un JSON mas. Eso permite que escucha_output lo compile y lo copie al portapapeles automaticamente, sin que el usuario tenga que buscarlo. El usuario puede editarlo sin tocar Python.

### 7.3 Cuatro procesos coordinados

WAIO v3.0 Consolidado opera con cuatro procesos: motor, visor, TRANSCLIP, escucha_output. Cada uno tiene una responsabilidad clara y su propio trigger de parada. El visor actua como coordinador: lanza escucha_output automaticamente y crea todos los triggers al cerrarse.

### 7.4 Menu contextual numerado

Los prefijos `01_`, `02_`, `03_`, `04_` fuerzan el orden alfabetico en Windows. Sin ellos, el orden es aleatorio.

### 7.5 Herramientas de diagnostico

`ver_estado.bat` y `limpiar_waio.bat` dan al usuario visibilidad del estado del sistema y una via rapida de limpieza si algo queda colgado. No existian en versiones anteriores.

### 7.6 Preparacion para publicar

La aparicion de `.gitignore`, `LICENSE` (MIT) y `requirements.txt` marca la intencion de publicar. Es la primera version con estos archivos.

---

## 8. Limitaciones Conocidas

- **Windows-only.** Usa `winreg`, `tasklist`, `clip`, `ctypes.windll` y el menu contextual de Windows.
- **Sin autenticacion.** Cualquier archivo JSON que caiga en Downloads es procesado. No hay firma ni validacion de origen.
- **Sin limite de acciones por transaccion.** Un payload con 1000 acciones se ejecuta completo.
- **Log sin rotacion.** Los logs crecen indefinidamente. Cada proceso crea su propio archivo con timestamp, pero no hay limpieza automatica.
- **El visor no distingue transacciones.** Muestra todos los JSON de `output/` en orden cronologico. No agrupa por `transaccion_id`.
- **TRANSCLIP solo lee texto del portapapeles.** No soporta imagenes ni archivos binarios.
- **Timeout fijo de 5 segundos** en escucha_output. No es configurable por el usuario.

---

## 9. Proximas Mejoras Sugeridas

Documentadas para una eventual v3.1 o v4.

### Prioridad alta
- Setear `total_acciones` en el motor para que escucha_output muestre contexto completo.
- Corregir los typos de `iniciar_escucha_output.bat`.
- `leer_resultados`: comando para que la IA lea sus propios resultados sin intervencion humana.

### Prioridad media
- Sistema de autenticacion por token temporal (diseno existente en `WAIO_SEGURIDAD_V2.5.md`, no implementado).
- Soporte de wildcards (`*.txt`, `*.py`).
- Log rotativo con limite de tamaño.

### Prioridad baja
- Interfaz web en puerto local.
- Cola persistente en disco.
- Sistema de plugins para comandos externos.

---

## 10. Conclusion

WAIO v3.0 Consolidado es la primera version que se considero lista para publicar. No trae un cambio conceptual de fondo, sino que **consolida** lo que ya existia: corrige bugs arrastrados, resuelve la saturacion del portapapeles con `escucha_output`, externaliza el prompt y agrega herramientas de diagnostico.

Los cuatro procesos coordinados (motor, visor, TRANSCLIP, escucha_output) forman un sistema completo. Los bugs conocidos son menores y estan todos documentados. Las limitaciones son conscientes.

El proyecto queda en un punto de madurez suficiente para su primera publicacion.

---

Documento elaborado: 2026-10-12
Version auditada: WAIO v3.0 Consolidado
Estado: Completo y listo para publicar.
