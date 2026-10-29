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
At WAIO we believe in transparency. Known risks of the autonomous agent paradigm are documented in the `/papers/` folder:
- **Reverse Prompt Injection (PCA):** The ability to inject malicious instructions through file names in the working directory. Documented in `INFORME_FALLA_SEGURIDAD_CONTEXTO_PASIVO.md`.
- **Mitigation:** A "File Name Sanitizer" is being developed for future versions.

## 4. Implemented Mitigations (v3.3)
- **Security Profiles:** `readonly`, `standard`, `advanced`, `debug`.
- **Dynamic Sandbox:** The AI only operates within the folder where WAIO was started.
- **Reserved Names Blacklist:** Blocking names like `CON`, `NUL`, `PRN`, and Alternate Data Streams (ADS) to prevent system hangs.
- **Path Validation:** Blocking Path Traversal (`../`) and absolute paths in lower profiles.
- **Secure Deletion:** Everything goes to the Recycle Bin by default.
- **Dual-Thread Engine:** The engine does not hang if a JSON is invalid.

## 5. User Responsibility (MIT License)
WAIO is distributed under the **MIT** license, which means it is provided **"AS IS"**, without warranties of any kind. 
The user is solely responsible for the use they give to the tool and third-party skills. WAIO is not responsible for direct or indirect damages, data loss, or malicious use of the software.