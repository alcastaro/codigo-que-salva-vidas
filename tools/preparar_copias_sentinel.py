"""Guarda copias pequeñas de lo que la Pista B lee de Sentinel, para usarlas si la red va lenta.

    data/sentinel/black_river.npz:
      rgb_antes, rgb_despues  uint8 (alto, ancho, 3)
      ndvi_antes, ndvi_despues  int8 (×100)
      db_antes, db_despues  int8 (dB redondeados)
"""
import sys
import time
from pathlib import Path

import numpy as np

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "taller"))
import ayuda  # noqa: E402

bbox = ayuda.caja(18.04, -77.82, 10)
t = time.time()
s2 = ayuda.buscar_escenas("sentinel-2-l2a", bbox, "2025-10-15/2025-11-10", max_nubes=60)
A = ayuda.sentinel2(list(s2[s2.fecha.str.startswith("2025-10-20")].item), bbox)
D = ayuda.sentinel2(list(s2[s2.fecha.str.startswith("2025-10-30")].item), bbox)
print("Sentinel-2 %.0fs" % (time.time() - t))
t = time.time()
s1 = ayuda.buscar_escenas("sentinel-1-rtc", bbox, "2025-10-10/2025-11-05", catalogo=ayuda.PLANETARY)
a = ayuda.radar_db(s1[(s1.orbita == 150) & s1.fecha.str.startswith("2025-10-17")].item.iloc[0], bbox)
d = ayuda.radar_db(s1[(s1.orbita == 150) & s1.fecha.str.startswith("2025-10-29")].item.iloc[0], bbox)
print("Sentinel-1 %.0fs" % (time.time() - t))

u8 = lambda x: (np.nan_to_num(x) * 255).round().astype("uint8")  # noqa: E731
i8 = lambda x, k=1: np.clip(np.nan_to_num(x * k, nan=-128), -128, 127).round().astype("int8")  # noqa: E731
out = RAIZ / "data" / "sentinel"
out.mkdir(parents=True, exist_ok=True)
np.savez_compressed(out / "black_river.npz",
                    rgb_antes=u8(A["rgb"]), rgb_despues=u8(D["rgb"]),
                    ndvi_antes=i8(A["ndvi"], 100), ndvi_despues=i8(D["ndvi"], 100),
                    db_antes=i8(a), db_despues=i8(d))
print("ok", (out / "black_river.npz").stat().st_size // 1024, "KB")
