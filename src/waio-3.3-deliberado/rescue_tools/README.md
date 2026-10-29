# rescue_tools — Herramientas de rescate de WAIO

Carpeta con scripts de emergencia. Se ejecutan con doble clic **solo
cuando algo salió mal** y el visor o el menú contextual no alcanzan.

Ninguno de estos scripts se expone en el menú contextual. No se
ejecutan en el ciclo normal de WAIO.

---

## kill_waio.py

**Qué hace:** detiene **TODO** WAIO de raíz, por capas de agresión
creciente. Es el botón de pánico.

### Estrategia por capas

1. **Capa 1 (básica):**
   - Crea los 4 triggers de parada (`STOP`, `TRANSCLIP_STOP`,
     `ESCUCHA_STOP`, `EVENTS_STOP`).
   - Espera 3 segundos a que los procesos que los vean se apaguen solos.
   - Lee cada lock conocido (`waio.lock`, `escucha.lock`,
     `transclip.lock`, `events.lock`, `voz.lock`), y si el PID existe
     y es Python, lo mata con `taskkill /F /T`.
   - Borra cada lock después de matar el PID (o si el PID no existe).
   - Borra los 4 triggers.

2. **Capa 2 (profunda):**
   - Solo se ejecuta si después de Capa 1 quedan procesos WAIO vivos.
   - Busca `python.exe`/`pythonw.exe` con nombres de WAIO en la línea
     de comandos (`.waio`, `waio_visor`, `waio_escucha`,
     `escucha_output`, `transclip`, `event_visor`, etc.).
   - Los mata con `taskkill /F /T`.
   - **Refuerzo:** si no encuentra ninguno por cmdline, mata **todos**
     los `pythonw.exe` (suelen ser el visor y los satélites).
   - Captura el visor, que no tiene lock propio.

3. **Capa 3 (total):**
   - Solo se ejecuta si después de Capa 2 quedan procesos WAIO vivos.
   - Mata **todos** los `python.exe`/`pythonw.exe` del sistema, con
     `taskkill /F /T` (árbol completo).
   - **Advertencia:** esto mata otros scripts Python ajenos a WAIO.

4. **Capa 3b (extrema):**
   - Solo se ejecuta si después de Capa 3 quedan procesos WAIO vivos.
   - Busca `cmd.exe`, `powershell.exe`, `pwsh.exe`, `conhost.exe` con
     nombres de WAIO en cmdline, y los mata.
   - Cubre el caso raro de un proceso no-Python que lanzó algo de WAIO.

### Reglas de seguridad

- **Nunca mata el propio proceso** (`os.getpid()`). Se loguea como
  `[SKIP] PID XXXX es el propio kill_waio`.
- **Log a archivo desde el inicio**, en
  `temp/logs/kill_waio_YYYYMMDD_HHMMSS.log`, con `flush` después de
  cada línea. Si el script muere, el log queda.
- **Pausa siempre al final** (`input()` en `finally`), aunque el
  script crashee.
- **No se suicida:** el propio `kill_waio.py` tiene `.waio` en su
  cmdline (vive en `.waio/rescue_tools/`). La función de detección
  lo excluye explícitamente.
- **No vacía `temp/jsonout/` ni `temp/output/`.** Esos son outputs
  de WAIO; `kill_waio` no los toca.

### Cuándo usarlo

- **WAIO se tildó** (cuelgue en `open(CON)`, script que no termina,
  timeout largo).
- **WAIO entró en bucle** (JSONs que se reprocesan, IDs duplicados).
- **Querés detener todo y empezar de limpio.**
- **El visor o los satélites quedaron huérfanos** después de un cuelgue.

### Uso
