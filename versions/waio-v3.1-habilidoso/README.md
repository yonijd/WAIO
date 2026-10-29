# WAIO v3.1 Habilidoso - Web AI Orchestrator

WAIO (Web AI Orchestrator) es un motor de automatizacion local y orquestador de comandos disenado para interactuar de forma directa entre modelos de IA (interfaces web/chatbots) y el sistema de archivos local de Windows.

La version 3.1 Habilidoso es un **cambio de paradigma** respecto a versiones anteriores. Introduce:

- **Sistema de habilidades**: comandos extensibles definidos en JSON + Python.
- **Perfiles de seguridad**: cuatro niveles de permisos configurables.
- **WispOut**: sistema de respuestas formateadas que da contexto a la IA.
- **Event Visor**: monitor de eventos del sistema de archivos.
- **Speech**: lectura por voz de los resultados.

---

## 1. QUE CARACTERIZA A ESTA VERSION

### Sistema de habilidades

Cada comando de WAIO se define como una **habilidad** en la carpeta `habilidades/`. Una habilidad es una carpeta con dos archivos:

```
habilidades/nombre_habilidad/
├── nombre_habilidad.json    (definicion)
└── nombre_habilidad.py      (implementacion, si es de tipo script)
```

El JSON define:
- `nombre`, `version`, `autor`, `categoria`, `tags`
- `descripcion`
- `tipo`: `comando_interno` (lo maneja el motor) o `script` (se ejecuta como Python)
- `parametros`: diccionario de parametros esperados
- `perfil_minimo`: `solo_lectura`, `estandar`, `avanzado`, `sin_restricciones`

Al arrancar, el motor **indexa** todas las habilidades y genera `habilidades/habilidades.json` (catalogo maestro). La IA puede consultar la lista con `listar_habilidades`.

### Sistema de perfiles de seguridad

`waio_config.json` define **cuatro perfiles**:

| Perfil | Sandbox | Rutas absolutas | Borrado | Scripts |
|---|---|---|---|---|
| `solo_lectura` | Si | No | Papelera | No |
| `estandar` | Si | No | Papelera | No |
| `avanzado` | No | Si (excepto carpetas del sistema) | Papelera | Si |
| `sin_restricciones` | No | Si | Permanente | Si |

El perfil activo se define en `waio_config.json` y el motor lo recarga en cada ciclo del loop (se puede cambiar en caliente).

### WispOut

`wispout.json` define el **formato de las respuestas** que WAIO le devuelve a la IA:

- **Encabezado**: `WAIO 3.1 | avanzado | 10MB | papelera`
- **Recordatorio**: cada N acciones
- **Susurro**: cada N acciones
- **Respuestas especiales**: para cambios de perfil, comandos bloqueados y errores

Esto da a la IA **contexto continuo** sobre el estado del sistema.

### Event Visor

`event_visor.py` monitorea cambios en el sistema de archivos con `watchdog` y actualiza el recordatorio de WispOut con los eventos recientes. Se controla desde el boton EVENTS del visor.

### Speech

`speech.py` lee el ultimo JSON de `jsonout/` y lo pronuncia con `System.Speech.Synthesis` de Windows. Pensado para el comando `mensaje`.

---

## 2. COMPONENTES PRINCIPALES

- **waio_escucha.py**: Motor de escucha. Monitorea Downloads, ejecuta comandos, indexa habilidades y formatea respuestas.
- **waio_visor.py**: Interfaz grafica (GUI). 9 botones en ingles (CLEAN, OUTPUT, PROJECT, TRANSCLIP, LISTEN, EVENTS, COPY, CLEAN OUTPUT).
- **transclip.py**: Puente traductor de comandos simples para el portapapeles.
- **escucha_output.py**: Compilador de resultados con timeout de 5 segundos y sonido de confirmacion.
- **event_visor.py**: Monitor de eventos del sistema de archivos (watchdog).
- **speech.py**: Lector por voz.
- **stop_event_visor.py**: Detenedor de event_visor por PID.
- **kill_waio.py**: Detencion rapida del motor.
- **instalador_waio.py** / **instalar_waio.bat**: Instalacion automatica.
- **desinstalador_waio.py** / **desinstalar_waio.bat**: Limpieza completa.
- **iniciar_transclip.bat** / **detener_transclip.bat**: Control de TRANSCLIP.
- **iniciar_escucha_output.bat** / **detener_escucha_output.bat**: Control de escucha_output.
- **ver_estado.bat**: Diagnostico del sistema.
- **limpiar_waio.bat**: Mata todos los procesos y limpia triggers/locks.
- **waio_config.json**: Configuracion de perfiles.
- **wispout.json**: Configuracion de formato de respuestas.
- **prompt.txt**: Prompt maestro editable.
- **habilidades/**: Carpeta de habilidades.

---

## 3. REQUISITOS DEL SISTEMA

- **Sistema Operativo**: Windows 10 / Windows 11
- **Python**: Version 3.8 o superior instalada en el PATH.
- **Librerias externas** (opcionales):
  ```
  pip install send2trash   # borrado a Papelera
  pip install watchdog     # event_visor
  ```
  Si no estan instaladas, WAIO funciona con fallbacks.

---

## 4. INSTALACION Y USO

### Instalacion

1. Ejecuta `instalar_waio.bat`.
2. El instalador copia los scripts a `%USERPROFILE%\.waio\` y crea las subcarpetas (`logs/`, `output/`, `jsonout/`, `trash/`, `pyseguras/`, `pyhabilidades/`).
3. Se anaden **5 entradas** al menu contextual:
   - `01 Iniciar WAIO Aqui`
   - `02 Visor WAIO`
   - `03 TRANSCLIP (WhatsApp)`
   - `04 Escucha Output`
   - `05 Matar WAIO (motor)`

### Uso tipico

1. Clic derecho en una carpeta → **01 Iniciar WAIO Aqui**.
2. El motor arranca, indexa las habilidades y abre el Visor.
3. El Visor lanza `escucha_output` automaticamente.
4. El motor genera el prompt en `output/`.
5. `escucha_output` lo compila y lo copia al portapapeles.
6. Pegas el prompt en la IA.
7. La IA consulta `listar_habilidades` para ver los comandos disponibles.
8. La IA genera un JSON y lo guarda en Downloads.
9. WAIO lo ejecuta y los resultados se copian al portapapeles.

### Detencion

1. **Cerrando el visor**: crea los triggers de parada de todos los procesos.
2. **Ejecutando `kill_waio.py`**: solo detiene el motor.
3. **Menu contextual → 05 Matar WAIO**.
4. **Para TRANSCLIP**: `detener_transclip.bat` o boton en el visor.
5. **Para escucha_output**: `detener_escucha_output.bat` o boton LISTEN.
6. **Para event_visor**: boton EVENTS del visor.

---

## 5. COMANDOS DISPONIBLES

WAIO v3.1 tiene **20 comandos base** mas las habilidades de la carpeta `habilidades/`.

### Comandos base (siempre disponibles)

**Solo lectura:**
- `listar_directorio` (ruta)
- `leer_archivo` (ruta, limite?)
- `existe_archivo` (ruta)
- `obtener_tamano` (ruta)
- `fecha_modificacion` (ruta)
- `contar_lineas` (ruta)
- `leer_lineas` (ruta, inicio?, fin?)
- `buscar_archivos` (ruta, patron)

**Escritura (perfil estandar+):**
- `crear_archivo` (ruta, contenido)
- `crear_carpeta` (ruta)
- `mover_archivo` (origen, destino)
- `renombrar_archivo` (ruta, nombre_nuevo)
- `copiar_archivo` (origen, destino)
- `append_archivo` (ruta, contenido)

**Avanzado:**
- `eliminar_archivo` (ruta)
- `eliminar_carpeta` (ruta)
- `ejecutar_script` (script, parametros?)

**Internos:**
- `mensaje` (contenido)
- `listar_habilidades` (sin parametros)
- `indexar_habilidades` (sin parametros)

### Habilidades externas

Ademas, la carpeta `habilidades/` incluye mas de 40 skills como `abrir_archivo`, `analizar_proyecto`, `crear_excel`, `crear_word`, `leer_pdf`, `buscar_duplicados`, `calcular_hash`, `crear_zip`, `extraer_zip`, etc. Para ver la lista completa, ejecuta `listar_habilidades`.

---

## 6. ESTRUCTURA DEL PAYLOAD JSON

```json
{
  "transaccion_id": "tx_ejemplo_001",
  "acciones": [
    { "comando": "listar_directorio", "ruta": "." },
    { "comando": "listar_habilidades" },
    { "comando": "crear_carpeta", "ruta": "mi_proyecto" },
    { "comando": "crear_archivo", "ruta": "mi_proyecto/README.md", "contenido": "# Proyecto" },
    { "comando": "mensaje", "contenido": "Proyecto creado" }
  ]
}
```

**Reglas estrictas:**
- Siempre usa `transaccion_id` + `acciones`.
- Maximo 10 acciones por transaccion.
- Maximo 2 MB de JSON.
- Timeout por accion: 30 segundos.
- No uses caracteres de control como `\x00`.

---

## 7. POLITICA DE SEGURIDAD

- **Perfiles configurables**: el perfil activo define que comandos se pueden usar.
- **Sandbox por defecto**: en `solo_lectura` y `estandar`, todas las operaciones estan confinadas al `WORK_DIR`.
- **Rutas prohibidas**: en `avanzado` y superiores, se bloquean `C:\Windows`, `C:\Program Files`, etc.
- **Borrado seguro**: los comandos de eliminacion usan Papelera o `trash/` manual.
- **Escritura atomica**: los JSON de resultado se escriben a `.tmp` y luego se renombran.
- **Portapapeles Unicode**: los resultados se copian con `ctypes` UTF-16.
- **Instancia unica**: TRANSCLIP, escucha_output y event_visor usan locks con PID.
- **Auditoria de logs**: cada proceso escribe en `%USERPROFILE%\.waio\logs\`.

---

## 8. ESTRUCTURA DE DIRECTORIOS

```
%USERPROFILE%\.waio\
├── waio_escucha.py              # Motor
├── waio_visor.py                # Visor
├── transclip.py                 # Puente WhatsApp
├── escucha_output.py            # Compilador
├── event_visor.py               # Monitor de eventos
├── speech.py                    # Lector por voz
├── kill_waio.py                 # Kill motor
├── prompt.txt                   # Prompt editable
├── waio_config.json             # Perfiles
├── wispout.json                 # Formato de respuestas
├── habilidades\                 # Skills (JSON + py)
│   └── habilidades.json         # Catalogo maestro
├── pyhabilidades\               # Scripts de skills copiados
├── pyseguras\                   # Scripts del usuario
├── logs\                        # Logs
├── output\                      # Resultados
├── jsonout\                     # JSONs procesados
└── trash\                       # Papelera manual
```

---

## 9. LICENCIA

MIT License. Ver archivo `LICENSE` para el texto completo.
