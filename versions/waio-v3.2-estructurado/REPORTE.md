# REPORTE TECNICO - WAIO v3.2 Estructurado

Auditoria tecnica de la version 3.2 Estructurado del motor WAIO (Web AI Orchestrator).

---

## 1. Ficha Tecnica

| Campo | Valor |
|---|---|
| Version | v3.2 Estructurado |
| Fecha de auditoria | 2026-10-12 |
| Archivos en raiz | 9 (+ 6 carpetas) |
| Skills indexadas | 47 (21 base + 26 usuario) |
| Plataforma objetivo | Windows 10/11 |
| Lenguaje | Python 3.8+ |
| Dependencias externas | `send2trash` opcional, `watchdog` opcional |
| Licencia | MIT |

---

## 2. Que caracteriza a v3.2

**v3.2 es un cambio de paradigma estructural.** No es una feature nueva ni una correccion: es la reorganizacion completa del proyecto.

### 2.1 El cambio principal: todo en carpetas

| Aspecto | v3.1 Habilidoso | v3.2 Estructurado |
|---|---|---|
| Comandos base | En codigo Python (`COMANDOS_BASE`) | En `core/` (una carpeta por comando) |
| Skills de usuario | En `habilidades/` | En `skills/` |
| Catalogo | `habilidades/habilidades.json` | `data/skills.json` |
| Configuracion | En la raiz | En `config/` |
| Temporales | En la raiz (`output/`, `logs/`, `jsonout/`) | En `temp/` |
| Herramientas de rescate | En la raiz | En `rescue_tools/` |

**El motor ya no contiene logica de comandos.** Todo comando es un JSON en `core/` o `skills/`. El motor solo lee, valida y ejecuta.

### 2.2 Comandos unificados

v3.2 simplifica los nombres de comandos especiales:

| v3.1 | v3.2 |
|---|---|
| `listar_habilidades` | `skills` |
| `indexar_habilidades` | `indexar` |
| `ejecutar_script` | `ejecutar` |
| (no existia) | `ayuda` |

Cada comando especial es **una sola palabra**. Los alias tambien se simplificaron.

### 2.3 Instalador por carpetas

v3.2 copia **carpetas enteras** en lugar de archivos sueltos:

```python
CARPETAS_A_COPIAR = ["core", "skills", "rescue_tools", "config", "data", "temp", "trash"]
```

Esto replica la estructura completa en `.waio/` y elimina la necesidad de listar archivo por archivo.

### 2.4 `kill_waio.py` en `rescue_tools/`

El kill switch se movio a `rescue_tools/`. El instalador fue actualizado para apuntar a `rescue_tools/kill_waio.py` en el menu contextual.

---

## 3. Arquitectura

WAIO v3.2 opera con **cinco procesos coordinados**:

1. **Motor** (`waio_escucha.py`): escucha Downloads, lee `config/`, ejecuta comandos desde `core/` y `skills/`.
2. **Visor** (`waio_visor.py`): interfaz grafica, monitorea `temp/output/`.
3. **TRANSCLIP** (`transclip.py`): puente de portapapeles.
4. **Escucha Output** (`escucha_output.py`): compilador de resultados con sonido.
5. **Event Visor** (`event_visor.py`): monitor de eventos con `watchdog`.

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
                             +--- indexa skills al arrancar
                             +--- carga config/waio_config.json
                             +--- carga config/wispout.json
                             +--- lanza waio_visor.py
                             |
                             | ejecuta comandos desde core/ y skills/
                             v
                    [WORK_DIR] (o absoluto si avanzado+)
                             |
                             | guarda resultados formateados
                             v
                        [temp/output/]
                             |
                             | monitorea
                             v
                    [escucha_output.py] ---> [Portapapeles]
                             |
                             v
                     Usuario pega a la IA
```

---

## 4. Estructura de Carpetas

```
waio-v3.2-estructurado/
├── config/                    # waio_config.json, wispout.json, prompt.txt
├── core/                      # 21 comandos base (uno por carpeta)
├── data/                      # skills.json (catalogo generado)
├── rescue_tools/              # kill_waio.py + bats + stop_monitor.py
├── skills/                    # 26 skills de usuario
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
├── README.md                  # Guia de uso
├── LICENSE                    # MIT
├── requirements.txt           # Dependencias
└── .gitignore                 # Exclusiones
```

---

## 5. Comandos

### 5.1 Comandos base (21, en `core/`)

Siempre disponibles sin importar perfil:

**Lectura:**
`listar_directorio`, `leer_archivo`, `existe_archivo`, `obtener_tamano`, `fecha_modificacion`, `contar_lineas`, `leer_lineas`, `buscar_archivos`

**Escritura:**
`crear_archivo`, `crear_carpeta`, `mover_archivo`, `renombrar_archivo`, `copiar_archivo`, `append_archivo`, `eliminar_archivo`, `eliminar_carpeta`

**Especiales:**
`skills`, `ayuda`, `indexar`, `ejecutar`, `mensaje`

### 5.2 Skills de usuario (26, en `skills/`)

| Skill | Funcion |
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

## 6. El indexador

`core/indexar/indexar.py` escanea `core/` y `skills/`, valida cada JSON y genera `data/skills.json`.

**Campos obligatorios por skill:**
- `nombre`, `version`, `autor`, `categoria`, `tags`
- `descripcion`, `tipo`, `parametros`, `perfil_minimo`

**Tipos validos:**
- `comando_interno`: el motor lo maneja directamente (ej: `skills`)
- `script`: se ejecuta via subprocess (ej: `listia`)

**Firma:** `WAIO-V5-SKILLS-2026`

---

## 7. Perfiles de seguridad

Los 4 perfiles estan definidos en `config/waio_config.json`:

| Perfil | Sandbox | Rutas absolutas | Borrado | Scripts |
|---|---|---|---|---|
| `solo_lectura` | Si | No | Papelera | No |
| `estandar` | Si | No | Papelera | No |
| `avanzado` | No | Si | Papelera | Si |
| `sin_restricciones` | No | Si | Permanente | Si |

---

## 8. Bugs conocidos

### 8.1 `transclip.py` dice `VERSION = "v2.6"`

El archivo `transclip.py` sigue declarando `v2.6` internamente. No se actualizo a 3.2.

**Impacto:** cosmetico. El titulo de la ventana de TRANSCLIP dice `TRANSCLIP - v2.6`.

### 8.2 `total_acciones` no seteado

`escucha_output.py` busca `total_acciones` en los JSONs, pero el motor no lo guarda.

**Impacto:** el encabezado del bloque compilado muestra `Accion X` sin el total.

### 8.3 `event_visor` instala `watchdog` automaticamente

Si `watchdog` no esta instalado, `event_visor.py` lo instala con `pip install`.

**Impacto:** puede sorprender al usuario en la primera ejecucion.

### 8.4 Race condition del `STOP.trigger`

El motor espera 1 segundo antes de borrar su propio `STOP.trigger`, pero el loop es de 2 segundos.

**Impacto:** dos motores pueden quedar corriendo brevemente.

---

## 9. Decisiones de diseño notables

### 9.1 Todo en carpetas

Cada comando y cada skill es una **carpeta** con un JSON de definicion y, opcionalmente, un `.py`. Esto permite:
- Versionar comandos individualmente
- Agregar comandos sin tocar el motor
- Validar comandos al indexar

### 9.2 Comandos como datos

Los comandos base estan en `core/` como JSON, no en codigo. El motor los lee. Esto significa que **agregar un comando es crear una carpeta**, no modificar Python.

### 9.3 Instalador por carpetas

El instalador copia carpetas enteras. Eso replica la estructura completa sin listar archivos.

### 9.4 `rescue_tools/` como caja de herramientas

Los `.bat` de control, `kill_waio.py` y `stop_monitor.py` viven juntos en `rescue_tools/`. Es la caja de herramientas del usuario.

### 9.5 `config/` versionado

`config/waio_config.json`, `config/wispout.json` y `config/prompt.txt` estan en el repo. El motor los crea si no existen, pero el repo tiene los originales como referencia.

---

## 10. Limitaciones conocidas

- **Windows-only.** Usa `winreg`, `tasklist`, `clip`, `ctypes.windll`.
- **Sin autenticacion.** Cualquier JSON en Downloads se procesa.
- **Sin rollback.** Si una accion falla, las siguientes se ejecutan igual.
- **Log sin rotacion.** Los logs crecen indefinidamente.
- **`event_visor` es fragil.** Instala dependencias, sobrescribe el recordatorio de WispOut.

---

## 11. Proximas mejoras

- Corregir `VERSION` en `transclip.py`.
- Setear `total_acciones` desde el motor.
- Eliminar `event_visor` si no se consolida.
- Log rotativo.
- Autenticacion por token temporal (diseno existente).

---

## 12. Conclusion

WAIO v3.2 Estructurado es la version donde el proyecto **se organiza definitivamente**. Los comandos dejan de estar en codigo y pasan a ser datos. Todo tiene su carpeta: comandos base en `core/`, skills en `skills/`, config en `config/`, catalogo en `data/`, temporales en `temp/`, herramientas en `rescue_tools/`.

No agrega features grandes. No corrige bugs criticos. **Reorganiza.** Y esa reorganizacion es lo que permite que las versiones futuras sean mas simples de mantener.

El nombre "Estructurado" lo captura perfectamente: el proyecto tiene estructura.

---

Documento elaborado: 2026-10-12
Version auditada: WAIO v3.2 Estructurado
Estado: Estructura completa y funcional.
