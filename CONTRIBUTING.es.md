# Contribuir a WAIO

¡Gracias por tu interés en contribuir a WAIO! El corazón de este proyecto no es el motor, sino **las skills**. Queremos que la comunidad crezca y cree sus propias habilidades para que cualquier IA web pueda hacer más cosas en el sistema.

## 🤝 ¿Cómo puedo contribuir?

Tenés varias formas de ayudar:

1. **Creando nuevas Skills:** La forma más valiosa. Si programaste un script en Python que resuelve un problema, adaptalo al formato de WAIO y compartilo.
2. **Mejorando el motor:** Si encontrás un bug en `waio_escucha.py`, `waio_visor.py` o en las herramientas de rescate, podés enviar un Pull Request.
3. **Reportando bugs:** Si algo falla, abrí un *Issue* con los logs y los pasos para reproducirlo.
4. **Mejorando la documentación:** Si ves un error en el README o en los papers, avisanos.

---

## 🛠️ Reglas para crear una Skill

Si querés enviar una skill nueva, **es obligatorio** que sigas el estándar documentado en [PROMPT_CREACION_SKILLS.md](PROMPT_CREACION_SKILLS.md). 

Los puntos críticos que revisaremos antes de aceptar tu Pull Request son:
1. **Salida de error:** Tu skill debe usar `sys.exit(1)` cuando falle, e imprimir el mensaje específico del error en `stdout`.
2. **Rutas relativas:** Debe leer `WAIO_WORKDIR` de las variables de entorno para resolver las rutas, sin usar rutas absolutas hardcodeadas.
3. **Metadatos:** El archivo `.json` debe tener el campo `"autor"` con tu nombre (o usuario de GitHub/Gitee) y el campo `"licencia": "MIT"`.
4. **Timeout:** Debe declarar el campo `timeout_segundos` en su JSON.

### Estructura de una Skill
```text
skills/nombre_de_tu_skill/
├── nombre_de_tu_skill.py     # El código
└── nombre_de_tu_skill.json   # El manifiesto (metadatos)