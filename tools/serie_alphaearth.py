"""Guarda la serie anual de AlphaEarth (2017–2025) de un lugar, comprimida en int8.

    .venv/bin/python tools/serie_alphaearth.py constanza 18.91 -70.745 4
"""
import sys
import time
from pathlib import Path

import numpy as np

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "taller"))
import ayuda  # noqa: E402

nombre, lat, lon, km = sys.argv[1], float(sys.argv[2]), float(sys.argv[3]), float(sys.argv[4])
ancho = int(sys.argv[5]) if len(sys.argv) > 5 else 300
bbox = ayuda.caja(lat, lon, km)
capas = {}
for anio in range(2017, 2026):
    t = time.time()
    e = ayuda.embeddings_alphaearth(bbox, anio, ancho)
    q = np.where(np.isnan(e), -128, np.sign(e) * np.sqrt(np.abs(e)) * 127.5)
    capas[f"a{anio}"] = np.clip(np.round(q), -128, 127).astype("int8")
    print(anio, "%.0fs" % (time.time() - t), flush=True)
destino = RAIZ / "data" / "alphaearth" / f"{nombre}_serie.npz"
np.savez_compressed(destino, bbox=np.array(bbox), **capas)
print("ok", destino.name, destino.stat().st_size // 1024, "KB")
