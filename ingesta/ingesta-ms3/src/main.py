import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from common import main
from extractor import extraer_viajes_y_pagos

if __name__ == "__main__":
    raise SystemExit(main("ms3", extraer_viajes_y_pagos))
