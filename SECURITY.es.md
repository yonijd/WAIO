# Política de Seguridad de WAIO

## 1. Nuestra Filosofía
WAIO es una herramienta de automatización local diseñada para darle "manos" a las IAs web. Reconocemos que el poder de ejecutar acciones en un sistema operativo conlleva riesgos. Por eso, el motor está diseñado con **seguridad por defecto**: sandbox por carpeta, perfiles de permisos, límites de escritura y borrado seguro a la papelera.

## 2. Reportar una Vulnerabilidad
Si descubrís una falla de seguridad en WAIO, por favor **NO abras un issue público**. 
Contactame directamente a: **[Tu Email o tu usuario de GitHub]**.
Me comprometo a:
1. Confirmar la recepción del reporte en un plazo máximo de 48 horas.
2. Investigar y desarrollar un parche si la falla es válida.
3. Darte el crédito correspondiente en el `CHANGELOG.md` cuando el parche sea publicado.

## 3. Riesgos Conocidos y Documentados
En WAIO creemos en la transparencia. Los riesgos conocidos del paradigma de agentes autónomos están documentados en la carpeta `/papers/`:
- **Prompt Injection Inverso (ACP):** La capacidad de inyectar instrucciones maliciosas a través de nombres de archivos en el directorio de trabajo. Documentado en `INFORME_FALLA_SEGURIDAD_CONTEXTO_PASIVO.md`.
- **Mitigación:** Se está trabajando en un "Sanitizador de Nombres de Archivos" para futuras versiones.

## 4. Mitigaciones Implementadas (v3.3)
- **Perfiles de Seguridad:** `readonly`, `standard`, `advanced`, `debug`.
- **Sandbox Dinámico:** La IA solo opera en la carpeta donde se inició WAIO.
- **Lista Negra de Nombres Reservados:** Bloqueo de nombres como `CON`, `NUL`, `PRN` y caracteres de flujo de datos (ADS) para evitar cuelgues del sistema.
- **Validación de Rutas:** Bloqueo de *Path Traversal* (`../`) y rutas absolutas en perfiles bajos.
- **Borrado Seguro:** Todo va a la Papelera de Reciclaje por defecto.
- **Motor Doble Hilo:** El motor no se cuelga si un JSON es inválido.

## 5. Responsabilidad del Usuario (Licencia MIT)
WAIO se distribuye bajo la licencia **MIT**, lo que significa que se proporciona **"AS IS" (tal cual)**, sin garantías de ningún tipo. 
El usuario es el único responsable del uso que le dé a la herramienta y a las skills de terceros. WAIO no se hace responsable por daños directos o indirectos, pérdida de datos o uso malintencionado del software.