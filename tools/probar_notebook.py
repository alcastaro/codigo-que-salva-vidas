"""Ejecuta en local las celdas de un notebook del taller y guarda cada figura en scratch/.

Salta las líneas `!pip`/`!wget` (en local ya están instaladas) y, si no hay GOOGLE_API_KEY,
las celdas que llaman a Gemini.

    .venv/bin/python tools/probar_notebook.py taller/pista_A_huracan.ipynb
"""
import os
import sys
import time
import traceback
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import nbformat

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "taller"))

nb = nbformat.read(sys.argv[1], as_version=4)
nombre = Path(sys.argv[1]).stem
salida = RAIZ / "scratch" / nombre
salida.mkdir(parents=True, exist_ok=True)
hay_key = bool(os.environ.get("GOOGLE_API_KEY"))

ns = {"display": print}
fig_n = 0


def guardar_figuras():
    global fig_n
    for num in plt.get_fignums():
        fig_n += 1
        plt.figure(num).savefig(salida / f"fig{fig_n:02d}.png", dpi=70)
    plt.close("all")


plt.show = guardar_figuras
fallos = 0
for i, c in enumerate(nb.cells):
    if c.cell_type != "code":
        continue
    if "pf.app(" in c.source:
        print(f"[{i}] (salto: lanza la app; se prueba aparte)")
        continue
    if not hay_key and ("cliente" in c.source):
        print(f"[{i}] (salto: necesita GOOGLE_API_KEY)")
        continue
    codigo = "\n".join(l for l in c.source.splitlines() if not l.lstrip().startswith("!"))
    t = time.time()
    try:
        exec(compile(codigo, f"celda{i}", "exec"), ns)
        guardar_figuras()
        print(f"[{i}] ok  {time.time() - t:5.1f}s")
    except Exception:
        fallos += 1
        print(f"[{i}] FALLO")
        traceback.print_exc()
print(f"\n{fallos} fallos · figuras en {salida.relative_to(RAIZ)}")
sys.exit(1 if fallos else 0)
