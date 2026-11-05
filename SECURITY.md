# WAIO Security Policy

## 1. Our Philosophy
WAIO is a local automation tool designed to give "hands" to web AIs. We recognize that the power to execute actions on an operating system carries risks. Therefore, the engine is designed with **security by default**: folder-based sandbox, permission profiles, write limits, and secure deletion to the recycle bin.

## 2. Reporting a Vulnerability
If you discover a security flaw in WAIO, please **DO NOT open a public issue**.
Contact me directly at: **[Your Email or GitHub username]**.
I commit to:
1. Confirming receipt of the report within a maximum of 48 hours.
2. Investigating and developing a patch if the flaw is valid.
3. Giving you the corresponding credit in the `CHANGELOG.md` when the patch is published.

## 3. Known and Documented Risks
At WAIO we believe in transparency. Known risks of the autonomous agent paradigm are documented in the `/papers/` folder.

The `REPORT_*_PASSIVE_CONTEXT_SECURITY_FLAW` series (Report 1, Report 2, and any subsequent reports) documents ongoing research into passive context injection: the ability to inject instructions through file names and other environment channels, without the user including them in the prompt. Subsequent reports expand on and validate previous ones; they do not replace them. Report 1 (`INFORME_FALLA_SEGURIDAD_CONTEXTO_PASIVO.md`) describes the initial finding; Report 2 (`INFORME_02_FALLA_SEGURIDAD_CONTEXTO_PASIVO_VALIDACION_Y_HALLAZGOS.md`) validates it experimentally and adds derived findings.

**Mitigation:** A "File Name Sanitizer" is being developed for future versions.

## 4. Implemented Mitigations (v3.3)
- **Security Profiles:** `readonly`, `standard`, `advanced`, `debug`.
- **Dynamic Sandbox:** The AI only operates within the folder where WAIO was started. There is no predictable canonical folder.
- **Reserved Names Blacklist:** Blocking names like `CON`, `NUL`, `PRN`, and Alternate Data Streams (ADS) to prevent system hangs.
- **Path Validation:** Blocking Path Traversal (`../`) and absolute paths in lower profiles.
- **Secure Deletion:** `eliminar_archivo` and `eliminar_carpeta` send files to the Recycle Bin. Overwrite (`crear_archivo` on an existing file), `append_archivo`, and `renombrar_archivo` are direct and do not go through the recycle bin in the `standard` profile. Users should avoid starting WAIO in folders containing files they cannot afford to lose.
- **Dual-Thread Engine:** The engine does not hang if a JSON is invalid.

## 5. User Responsibility (MIT License)
WAIO is distributed under the **MIT** license, which means it is provided **"AS IS"**, without warranties of any kind.
The user is solely responsible for the use they give to the tool and third-party skills. WAIO is not responsible for direct or indirect damages, data loss, or malicious use of the software.