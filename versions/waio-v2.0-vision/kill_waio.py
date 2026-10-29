import os
from pathlib import Path

waio_dir = Path(os.environ["USERPROFILE"]) / ".waio"
stop = waio_dir / "STOP.trigger"
stop.touch()

print("STOP.trigger creado. El motor WAIO se detendra en <2 segundos.")
print("(El visor continuara funcionando)")
input("\nPresione Enter para salir...")