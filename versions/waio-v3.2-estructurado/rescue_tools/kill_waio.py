# -*- coding: utf-8 -*-
import os
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.resolve()
stop = SCRIPT_DIR / "STOP.trigger"
stop.touch()

print("STOP.trigger creado. El motor WAIO se detendra en menos de 2 segundos.")
print("El visor continuara funcionando.")
input("\nPresione Enter para salir...")
