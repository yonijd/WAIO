# WAIO v3.2 Estructurado - Web AI Orchestrator

WAIO (Web AI Orchestrator) es un motor de automatizacion local y orquestador de comandos disenado para interactuar de forma directa entre modelos de IA (interfaces web/chatbots) y el sistema de archivos local de Windows.

La version 3.2 Estructurado reorganiza completamente el proyecto. Los comandos dejan de estar en codigo y pasan a ser datos. Todo tiene su carpeta: comandos base en `core/`, skills en `skills/`, config en `config/`, catalogo en `data/`, temporales en `temp/`, herramientas de rescate en `rescue_tools/`.

---

## 1. QUE CARACTERIZA A ESTA VERSION

### Todo en carpetas

Cada comando es una carpeta con un JSON de definicion. Cada skill tambien. Esto permite agregar funcionalidad sin tocar el motor: crear la carpeta, escribir el JSON y ejecutar `indexar`.

### Comandos unificados

Los comandos especiales se simplificaron:

- `skills` (antes `listar_habilidades`)
- `indexar` (antes `indexar_habilidades`)
- `ejecutar` (antes `ejecutar_script`)
- `ayuda` (nuevo)

### Instalador por carpetas

El instalador copia carpetas enteras en lugar de archivos sueltos. La estructura se replica integra en `.waio/`.

### Herramientas de rescate

`kill_waio.py`, `stop_monitor.py` y los `.bat` de control viven juntos en `rescue_tools/`.

---

## 2. COMPONENTES PRINCIPALES

- **waio_escucha.py**: Motor de escucha. Monitorea Downloads, ejecuta comandos desde `core/` y `skills/`.
- **waio_visor.py**: Interfaz grafica (GUI) de monitoreo en tiempo real.
- **transclip.py**: Puente traductor de comandos simples para el portapapeles.
- **escucha_output.py**: Compilador de resultados con timeout de 5s y sonido de confirmacion.
- **event_visor.py**: Monitor de eventos del sistema de archivos (watchdog).
- **instalador_waio.py** / **instalar_waio.bat**: Instalacion automatica en `%USERPROFILE%\.waio`.
- **desinstalador_waio.py** / **desinstalar_waio.bat**: Limpieza completa.
- **rescue_tools/**: Carpeta con herramientas de rescate.

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
2. El instalador copia todas las carpetas (`core/`, `skills/`, `config/`, `data/`, `rescue_tools/`, `temp/`, `trash/`) y los archivos sueltos a `%USERPROFILE%\.waio\`.
3. Se anaden 5 entradas al menu contextual:
   - **01 Iniciar WAIO**
   - **02 Visor**
   - **03 Transclip**
   - **04 Clip Output**
   - **05 Kill WAIO**

### Uso tipico

1. Clic derecho en una carpeta → **01 Iniciar WAIO**.
2. El motor arranca, indexa skills y abre el Visor.
3. El Visor lanza `escucha_output` automaticamente.
4. El motor genera el prompt en `temp/output/`.
5. `escucha_output` lo compila y lo copia al portapapeles.
6. Pegas el prompt en la IA.
7. La IA consulta `skills` para ver los comandos disponibles.
8. La IA genera un JSON y lo guarda en Downloads.
9. WAIO lo ejecuta y los resultados se copian al portapapeles.

### Detencion

1. **Cerrando el visor**: crea los triggers de parada de todos los procesos.
2. **Ejecutando `rescue_tools/kill_waio.py`**: solo detiene el motor.
3. **Menu contextual → 05 Kill WAIO**.
4. **Para TRANSCLIP**: `detener_transclip.bat` o boton en el visor.
5. **Para escucha_output**: `detener_escucha_output.bat` o boton LISTEN.
6. **Para event_visor**: boton EVENTS del visor.

---

## 5. ESTRUCTURA DEL PROYECTO

```
waio-v3.2-estructurado/
├── config/                    # waio_config.json, wispout.json, prompt.txt
├── core/                      # Comandos base (uno por carpeta)
├── data/                      # skills.json (catalogo generado)
├── rescue_tools/              # kill_waio.py + bats + stop_monitor.py
├── skills/                    # Skills de usuario (una por carpeta)
├── temp/                      # output/, logs/, jsonout/, workdir.txt, waio.lock
├── waio_escucha.py            # Motor
├── waio_visor.py              # Visor
├── escucha_output.py          # Compilador
├── event_visor.py             # Monitor de eventos
├── transclip.py               # Puente de portapapeles
├── instalador_waio.py         # Instalador
├── desinstalador_waio.py      # Desinstalador
├── instalar_waio.bat          # Lanzador del instalador
├── desinstalar_waio.bat       # Lanzador del desinstalador
├── README.md                  # Este archivo
├── REPORTE.md                 # Auditoria tecnica
├── CHANGELOG.md               # Historial de cambios
├── LICENSE                    # MIT
├── requirements.txt           # Dependencias
└── .gitignore                 # Exclusiones
```

---

## 6. COMANDOS DISPONIBLES

WAIO v3.2 tiene **47 comandos indexados**: 21 base (en `core/`) + 26 skills de usuario (en `skills/`).

### Comandos base (21, siempre disponibles)

**Lectura:**
- `listar_directorio` (listar, ls, dir)
- `leer_archivo` (leer, cat, read)
- `existe_archivo` (existe, test, exists)
- `obtener_tamano` (tamano, size)
- `fecha_modificacion` (modificado, modified)
- `contar_lineas` (contar, wc, count)
- `leer_lineas` (head, read_lines)
- `buscar_archivos` (buscar, find, search)

**Escritura:**
- `crear_archivo` (crear, touch, create)
- `crear_carpeta` (mkdir, make_dir)
- `mover_archivo` (mover, mv, move)
- `renombrar_archivo` (renombrar, rename, ren)
- `copiar_archivo` (copiar, cp, copy)
- `append_archivo` (agregar, append)
- `eliminar_archivo` (eliminar, rm, del, delete)
- `eliminar_carpeta` (rmdir, delete_dir)

**Especiales:**
- `skills`: lista las skills disponibles
- `ayuda` (help, ?): muestra la guia de comandos
- `indexar` (index): regenera `data/skills.json`
- `ejecutar` (run): ejecuta un script de `skills/` o `core/`
- `mensaje` (echo, say): emite un texto

### Skills de usuario (26, en `skills/`)

| Skill | Descripcion |
|---|---|
| `abrir_archivo` | Abre archivos con su programa asociado |
| `abrir_programa` | Abre programas por nombre |
| `analizar_proyecto` | Analiza estructura de carpetas |
| `buscar_contenido` | Busca texto dentro de archivos |
| `buscar_duplicados` | Encuentra archivos duplicados |
| `calcular_hash` | Calcula hash de archivos |
| `copiar_carpeta` | Copia carpetas recursivamente |
| `crear_excel` | Crea archivos Excel |
| `crear_word` | Crea archivos Word |
| `crear_zip` | Crea archivos ZIP |
| `deepia` | Listado JSON estructurado (pareja de `listia`) |
| `editar_archivo` | Edita lineas especificas |
| `ejecutar_comando` | Ejecuta comandos del sistema |
| `estado` | Muestra estado del sistema |
| `extlog` | Log extendido |
| `extraer_metadatos` | Extrae metadatos de archivos |
| `extraer_zip` | Extrae ZIPs |
| `grep_avanzado` | Busqueda avanzada con regex |
| `leer_excel` | Lee archivos Excel |
| `leer_pdf` | Lee archivos PDF |
| `leer_word` | Lee archivos Word |
| `listia` | Listado JSON simple (pareja de `deepia`) |
| `mostrar_arbol` | Arbol de directorios |
| `super_buscar` | Busqueda multi-criterio |
| `syslog` | Informacion del sistema |
| `verificar_paquetes` | Verifica paquetes Python |

---

## 7. ESTRUCTURA DEL PAYLOAD JSON

```json
{
  "transaccion_id": "tx_ejemplo_001",
  "acciones": [
    { "comando": "skills" },
    { "comando": "listar_directorio", "ruta": "." },
    { "comando": "crear_carpeta", "ruta": "mi_proyecto" },
    { "comando": "crear_archivo", "ruta": "mi_proyecto/README.md", "contenido": "# Proyecto" },
    { "comando": "ejecutar", "script": "listia", "parametros": ["--ruta=."] }
  ]
}
```

**Reglas estrictas:**
- Siempre usa `transaccion_id` + `acciones`.
- No uses caracteres de control como `\x00`.
- Usa los nombres exactos de parametros (`origen`/`destino`, no `ruta_origen`).

---

## 8. PERFILES DE SEGURIDAD

`config/waio_config.json` define cuatro perfiles:

| Perfil | Sandbox | Rutas absolutas | Borrado | Scripts |
|---|---|---|---|---|
| `solo_lectura` | Si | No | Papelera | No |
| `estandar` | Si | No | Papelera | No |
| `avanzado` | No | Si | Papelera | Si |
| `sin_restricciones` | No | Si | Permanente | Si |

El perfil activo se define en `config/waio_config.json` y el motor lo recarga en cada ciclo.

---

## 9. POLITICA DE SEGURIDAD

- **Perfiles configurables**: el perfil activo define que comandos se pueden usar.
- **Sandbox por defecto**: en `solo_lectura` y `estandar`, todas las operaciones estan confinadas al `WORK_DIR`.
- **Rutas prohibidas**: en `avanzado` y superiores, se bloquean `C:\Windows`, `C:\Program Files`, etc.
- **Borrado seguro**: los comandos de eliminacion usan Papelera o `trash/` manual.
- **Escritura atomica**: los JSON de resultado se escriben a `.tmp` y luego se renombran.
- **Portapapeles Unicode**: los resultados se copian con `ctypes` UTF-16.
- **Auditoria de logs**: cada proceso escribe en `temp/logs/`.

---

## 10. LICENCIA

MIT License. Ver archivo `LICENSE` para el texto completo.
