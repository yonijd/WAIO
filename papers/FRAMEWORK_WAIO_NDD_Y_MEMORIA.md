# FRAMEWORK WAIO: NOMENCLATURE-DRIVEN DEVELOPMENT (NDD)
**Proyecto:** WAIO (Web AI Orchestrator)  
**Autor:** Yonijd  
**Fecha:** 25 de Octubre de 2026  
**Propósito:** Definir el estándar de estructuración de proyectos para agentes autónomos basados en Contexto Pasivo y Memoria Semántica.

---

## 1. El Problema del Prompt Estático

En la programación tradicional (Python, C++, JS), tenemos estándares de carpetas (ej. `/src`, `/bin`, `/tests`) y archivos de configuración (`package.json`, `requirements.txt`). 

En el desarrollo de agentes de IA (Skills, Plugins), el problema es que cada vez que creamos un programa nuevo, tenemos que reescribir o adaptar el *System Prompt* para explicarle a la IA qué es el proyecto, qué archivos tiene, qué reglas sigue y cuál es su estado actual. Esto es ineficiente, quema tokens y genera errores.

**La solución:** El **Framework NDD**. En lugar de que el humano le explique el proyecto a la IA en el prompt, el **sistema de archivos mismo ES la explicación**. El entorno se convierte en el *System Prompt implícito*.

---

## 2. El Estándar NDD (Nomenclature-Driven Development)

El NDD propone que el nombre de cada carpeta y archivo sea una instrucción sintáctica. Para el desarrollo de nuevas Skills en WAIO, la estructura debe dictar el comportamiento.

### A. El Workdir como Sistema de Memoria
Para proyectos largos, no necesitamos una base de datos SQL. Usamos la **Memoria Semántica Pasiva**. El Workdir del proyecto almacena archivos de estado:

*   `estado_fase_actual_auditoria_de_seguridad.txt` 
*   `pendiente_optimizar_skill_de_voz.txt`
*   `memoria_la_ia_prefiere_responder_en_json.txt`
*   `recordatorio_no_usar_bootstrap_en_html.txt`

**¿Qué pasa cuando entra una nueva IA?** Hace un `listia`. Lee esos nombres. Y automáticamente **sabe en qué estado está el proyecto, qué falta y qué reglas no debe romper**, sin leer un solo archivo ni gastar tokens de contexto.

### B. El Diseño de Skills por "Legos"
Cuando desarrollamos una nueva skill (ej. `crear_pdf`), en lugar de darle instrucciones de uso en el prompt, creamos un micro-entorno:

*   `regla_pdf_usar_fuente_arial_12.txt`
*   `regla_pdf_margenes_2_5_cm.txt`
*   `entorno_pdf_modo_impresion_escala_grises.txt`

La IA construye la lógica de la skill uniendo estos "legos" de contexto. Si el usuario quiere cambiar el margen, no cambia el código Python; simplemente renombra el archivo a `margenes_3_cm.txt`.

---

## 3. Aplicación en Proyectos Largos (Contexto Macro)

En proyectos de múltiples meses, los chats se pierden y la IA olvida el contexto. Con NDD, el directorio se convierte en una **Bitácora Viva**.

### La Estructura de un Proyecto NDD:
```text
/proyecto_waio_skill_voz/
│
├── 00_CONTEXTO_GENERAL/
│   ├── objetivo_crear_skill_de_voz_con_tts_offline.txt
│   └── autor_usuario_principiante_sin_conocimientos_avanzados.txt
│
├── 01_ESTADO_ACTUAL/
│   ├── fase_1_completada_lectura_de_texto.txt
│   └── fase_2_pendiente_integracion_de_voces.txt
│
├── 02_REGLAS_ESTRICTAS/
│   ├── prohibido_usar_apos_nube_usar_offline.txt
│   └── ignorar_archivos_temporales_de_prueba.txt
│
└── 03_ASSETS/
    └── (imágenes, audios, etc.)
```

Cuando la IA entra al proyecto y ejecuta `listia`, su "cerebro" procesa los nombres y **se auto-inyecta el contexto macro**. Sabe que está en la fase 2, que debe ser offline y que el usuario no es experto. No necesita que se lo digan en el chat.

---

## 4. El Futuro: El Motor WAIO 4.0

Para que esto funcione a nivel masivo, el motor de WAIO debería tener un módulo que lea estos archivos y los inyecte en el JSON de respuesta. 

Imaginemos que el usuario le dice a la IA: *"Programa la skill de voz"*.
El motor de WAIO detecta los archivos en `/01_ESTADO_ACTUAL/` y `/02_REGLAS_ESTRICTAS/`, y le envía a la IA un JSON con un campo oculto:
> `"contexto_pasivo": ["fase_2_pendiente_integracion_de_voces", "prohibido_usar_apos_nube_usar_offline"]`

La IA lee ese JSON y escribe el código perfecto en el primer intento, porque el entorno le susurró las reglas.

---

## 5. Conclusión

El Framework NDD transforma la carpeta de trabajo (Workdir) en una **interfaz de programación semántica**. Ya no programamos escribiendo líneas de código o prompts kilométricos; **programamos ordenando y nombrando archivos**. Es el paso lógico hacia la creación de sistemas operativos diseñados para Inteligencias Artificiales.

*"El prompt es una orden; el contexto pasivo es un hábitat."*