# REPORTE TECNICO - WAIO v3.1 Habilidoso

Auditoria tecnica de la version 3.1 Habilidoso del motor WAIO (Web AI Orchestrator).

---

## 1. Ficha Tecnica

| Campo | Valor |
|---|---|
| Version | v3.1 Habilidoso |
| Fecha de auditoria | 2026-10-12 |
| Archivos en raiz | 21 |
| Carpeta adicional | `habilidades/` (48+ skills) |
| Tamaño total | ~133 KB (sin contar `habilidades/`) |
| Plataforma objetivo | Windows 10/11 |
| Lenguaje | Python 3.8+ |
| Dependencias externas | `send2trash` opcional, `watchdog` opcional |
| Licencia | MIT |

---

## 2. Que es v3.1 Habilidoso

v3.1 es un **cambio de paradigma** respecto a v3.0 Consolidado. No es una iteracion incremental: introduce cinco sistemas nuevos que transforman el modelo de operacion de WAIO.

### 2.1 Sistema de habilidades

Cada comando es una **habilidad** en la carpeta `habilidades/`. Una habilidad es una carpeta con un JSON de definicion y, opcionalmente, un script Python.

**Tipos de habilidad:**
- `comando_interno`: el motor lo maneja directamente (ej: `listar_habilidades`).
- `script`: se ejecuta con `subprocess.run([python, script] + parametros)` (ej: `abrir_archivo`).

**Indexacion:** al arrancar, el motor escanea `habilidades/`, valida cada JSON, copia los scripts a `pyhabilidades/` y genera `habilidades/habilidades.json` (catalogo maestro).

### 2.2 Sistema de perfiles

`waio_config.json` define cuatro perfiles de seguridad:

| Perfil | Sandbox | Rutas absolutas | Borrado | Scripts | Límite escritura |
|---|---|---|---|---|---|
| `solo_lectura` | Si | No | Papelera | No | 0 B |
| `estandar` | Si | No | Papelera | No | 1 MB |
| `avanzado` | No | Si | Papelera | Si | 10 MB |
| `sin_restricciones` | No | Si | Permanente | Si | Sin límite |

El motor recarga la config en cada ciclo del loop, por lo que se puede cambiar de perfil en caliente.

### 2.3 WispOut

`wispout.json` define el formato de las respuestas. Agrega:
- **Encabezado** en cada respuesta: `WAIO 3.1 | avanzado | 10MB | papelera`
- **Recordatorio** cada 5 acciones
- **Susurro** cada 3 acciones
- **Respuestas especiales** para cambios de perfil y errores

Esto da a la IA **contexto continuo** sobre el estado del sistema.

### 2.4 Event Visor

`event_visor.py` monitorea cambios en el sistema de archivos con `watchdog` y actualiza el recordatorio de WispOut con los eventos recientes. Se controla desde el boton EVENTS del visor.

### 2.5 Speech

`speech.py` lee el ultimo JSON de `jsonout/` y lo pronuncia con `System.Speech.Synthesis`. Pensado para el comando `mensaje`.

---

## 3. Arquitectura

WAIO v3.1 opera con **cinco procesos coordinados**:

1. **Motor** (`waio_escucha.py`): escucha, ejecuta, indexa, formatea.
2. **Visor** (`waio_visor.py`): interfaz grafica con 9 botones.
3. **TRANSCLIP** (`transclip.py`): puente de portapapeles.
4. **Escucha Output** (`escucha_output.py`): compilador con sonido.
5. **Event Visor** (`event_visor.py`): monitor de eventos.

Ademas, `speech.py` se lanza por separado para leer resultados por voz.

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
                    [waio_escucha.py]
                             |
                             +--- indexa habilidades al arrancar
                             +--- carga waio_config.json
                             +--- carga wispout.json
                             +--- lanza waio_visor.py
                             |
                             | ejecuta acciones
                             v
                    [WORK_DIR] (o absoluto si avanzado+)
                             |
                             | guarda resultados formateados
                             v
                        [output/]
                             |
                             | monitorea
                             v
                    [escucha_output.py] ---> [Portapapeles]
                             |
                             v
                     Usuario pega a la IA
```

---

## 4. Flujo de Carpetas

WAIO v3.1 gestiona **seis carpetas** dentro de `%USERPROFILE%\.waio\`:

| Carpeta | Proposito |
|---|---|
| `habilidades/` | Skills (JSON + .py) + catalogo maestro |
| `pyhabilidades/` | Scripts de skills copiados por el indexador |
| `pyseguras/` | Scripts del usuario ejecutables |
| `logs/` | Logs de todos los procesos |
| `output/` | Resultados formateados |
| `jsonout/` | JSONs procesados |
| `trash/` | Papelera manual |

**Archivos de control:**

| Archivo | Proposito |
|---|---|
| `prompt.txt` | Prompt editable |
| `waio_config.json` | Perfiles |
| `wispout.json` | Formato de respuestas |
| `workdir.txt` | Directorio de trabajo actual (para el boton PROJECT) |
| `transclip.lock`, `escucha.lock`, `events.lock` | Locks de instancia |
| `STOP.trigger`, `TRANSCLIP_STOP.trigger`, `ESCUCHA_STOP.trigger`, `EVENTS_STOP.trigger` | Senales de parada |

---

## 5. Evolucion respecto a v3.0

| Area | v3.0 Consolidado | v3.1 Habilidoso | Tipo |
|---|---|---|---|
| Comandos | 12 | 20 base + 48 skills | Crecimiento masivo |
| Sistema de skills | No | Si | Feature nueva |
| Perfiles de seguridad | No | 4 perfiles | Feature nueva |
| Config externa | No | `waio_config.json` | Feature nueva |
| WispOut | No | Si | Feature nueva |
| TTS | No | `speech.py` | Feature nueva |
| Event monitor | No | `event_visor.py` | Feature nueva |
| Comandos nuevos | — | `append_archivo`, `renombrar_archivo`, `contar_lineas`, `leer_lineas`, `buscar_archivos`, `ejecutar_script`, `listar_habilidades`, `indexar_habilidades` | 8 nuevos |
| Visor botones | 6 | 9 | Crecimiento |
| Menu contextual | 4 entradas | 5 entradas | Crecimiento |
| Motor | 28 KB | 65 KB | Mas que duplicado |
| Procesos coordinados | 4 | 5 (+event_visor) | Crecimiento |

### Conclusion de la evolucion

v3.1 no es una mejora incremental de v3.0: es una **refundacion**. Pasa de "motor con comandos fijos" a "motor extensible con skills definidas por el usuario". Los perfiles de seguridad agregan un modelo de permisos configurable. WispOut transforma la comunicacion con la IA de "resultado suelto" a "resultado con contexto".

---

## 6. Bugs Conocidos

v3.1 fue una **version de transicion**. Muchos componentes quedaron a medio camino. Los bugs documentados son:

### 6.1 Instalador no copia los archivos nuevos

`instalador_waio.py` de v3.1 no incluye en `FILES_TO_COPY`:
- `event_visor.py`
- `speech.py`
- `stop_event_visor.py`

**Impacto:** el visor (que vive en `.waio/`) no encuentra esos archivos. El boton EVENTS no funciona en instalaciones reales.

### 6.2 Desinstalador desactualizado (corregido en auditoria)

El `desinstalador_waio.py` original decia `VERSION = "3.0"` y borraba solo 4 entradas del menu, dejando huerfanas `02_visor` y `05_kill_waio`.

**Estado:** corregido durante la auditoria. Ahora dice `VERSION = "3.1"` y borra las 5 entradas.

### 6.3 `limpiar_waio.bat` no limpia event_visor

No borra `events.lock` ni `EVENTS_STOP.trigger`. Si `event_visor` estaba corriendo, el lock queda huerfano.

### 6.4 `ver_estado.bat` no reporta event_visor

No chequea `events.lock` ni `EVENTS_STOP.trigger`, ni incluye `event_visor.py` en la lista de archivos clave.

### 6.5 `stop_event_visor.py` busca el PID en el archivo equivocado

`stop_event_visor.py` busca `event_visor.pid`, pero `event_visor.py` crea `events.lock`. **No funciona.**

**Nota:** `event_visor` se controla desde el visor con `EVENTS_STOP.trigger`, asi que este script no se usa realmente.

### 6.6 `speech.py` lee el campo equivocado

`speech.py` lee el campo `contenido` del ultimo JSON de `jsonout/`. Pero la mayoria de los JSONs de resultado tienen `output`, no `contenido`. Solo funciona con el comando `mensaje`.

### 6.7 Typos en `iniciar_escucha_output.bat` (heredados de v3.0)

- `chcp 65001 nul` (falta `>`)
- `timeout t 2 nobreak nul` (faltan `/`)

**Impacto:** cosmetico. El `.bat` lanza `escucha_output.py` igual.

### 6.8 Race condition del `STOP.trigger` (heredada de v2.0)

El motor nuevo espera 1 segundo antes de borrar su propio `STOP.trigger`, pero el loop del motor anterior es de 2 segundos. Pueden quedar dos motores corriendo brevemente.

### 6.9 `total_acciones` no seteado (heredado de v3.0)

`escucha_output.py` busca `total_acciones` en los JSONs, pero el motor no lo guarda. Cae al formato sin total.

---

## 7. Decisiones de Diseño Notables

### 7.1 Skills como unidad de extension

En lugar de agregar comandos al motor, cada comando es una skill. Eso permite que el usuario agregue funcionalidad sin tocar el codigo del motor. Las skills se versionan, categorizan y validan.

### 7.2 Perfiles en JSON externo

Los perfiles viven en `waio_config.json`, no en el codigo. Se pueden modificar sin recompilar. El motor los recarga en cada ciclo.

### 7.3 WispOut como capa de presentacion

La IA no ve el resultado crudo: ve un bloque con encabezado, cuerpo, recordatorio y susurros. Eso da contexto continuo sin que la IA tenga que preguntar.

### 7.4 Indexacion automatica al arrancar

El motor indexa `habilidades/` cada vez que arranca. Eso garantiza que el catalogo este siempre actualizado, a costa de un tiempo de arranque mayor.

### 7.5 Formato de respuestas del comando `mensaje`

A diferencia de otros comandos, `mensaje` no toca el sistema de archivos: solo emite un texto. Esta pensado para que la IA se comunique directamente con el usuario (y `speech.py` lo lea en voz alta).

---

## 8. Limitaciones Conocidas

- **Windows-only.** Usa `winreg`, `tasklist`, `clip`, `ctypes.windll`, `os.startfile`.
- **Sin autenticacion.** Cualquier JSON en Downloads se procesa.
- **Sin rollback.** Si una accion falla, las siguientes se ejecutan igual.
- **Log sin rotacion.** Los logs crecen indefinidamente.
- **El visor no distingue transacciones.** Muestra todos los JSONs de `output/` en orden cronologico.
- **`event_visor` es fragil.** Instala `watchdog` automaticamente, sobrescribe el recordatorio de WispOut, y no se puede detener con `stop_event_visor.py`.
- **Las skills externas no tienen sandbox propio.** Una skill de tipo `script` corre con los permisos del motor.

---

## 9. Proximas Mejoras Sugeridas

Documentadas para v3.2:

- Refundir el sistema de skills en algo mas simple.
- Eliminar `event_visor` (resulto inutil).
- Integrar `speech` al flujo principal.
- Corregir los bugs del instalador y desinstalador.
- Actualizar `limpiar_waio.bat` y `ver_estado.bat`.
- Setear `total_acciones` desde el motor.

---

## 10. Conclusion

WAIO v3.1 Habilidoso es una **version de transicion con un salto conceptual enorme**. Introduce skills, perfiles, WispOut, event_visor y speech. Algunos de esos sistemas quedaron a medio camino (event_visor, speech) y otros se consolidaron (skills, perfiles).

No es una version estable. Es el puente entre v3.0 Consolidado y la version que consolida el cambio de paradigma. Su valor esta en **haber explorado el territorio**: probo que se pueden tener skills extensibles, perfiles configurables y respuestas con contexto. Eso sento las bases para lo que vino despues.

---

Documento elaborado: 2026-10-12
Version auditada: WAIO v3.1 Habilidoso
Estado: Version de transicion documentada.
