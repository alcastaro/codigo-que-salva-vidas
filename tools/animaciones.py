"""Animaciones GIF propias para el deck, hechas con los datos del taller (sin capturar webs).

    .venv/bin/python tools/animaciones.py melissa radar alphaearth_serie:constanza
"""
import io
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "taller"))
import ayuda  # noqa: E402

OUT = RAIZ / "deck" / "capturas"
NEGRO, AZUL, ROJO, AMARILLO, CELESTE = "#1e1e1e", "#4285f4", "#ea4335", "#f9ab00", "#57caff"
plt.rcParams.update({"font.family": ["Google Sans", "DejaVu Sans"], "font.size": 13})


def a_imagen(fig) -> Image.Image:
    b = io.BytesIO()
    fig.savefig(b, format="png", dpi=100, facecolor=fig.get_facecolor())
    plt.close(fig)
    b.seek(0)
    return Image.open(b).convert("RGB")


def guardar_gif(cuadros, nombre, ms=120, pausa_final=1500):
    duraciones = [ms] * (len(cuadros) - 1) + [pausa_final]
    pal = [c.quantize(colors=128, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE) for c in cuadros]
    pal[0].save(OUT / f"{nombre}.gif", save_all=True, append_images=pal[1:], duration=duraciones, loop=0, optimize=True)
    print(nombre, (OUT / f"{nombre}.gif").stat().st_size // 1024, "KB")


def melissa():
    ens = ayuda.leer_weatherlab("data/melissa/weatherlab_FNV3P2_ensemble_2025_10_25T00.csv")
    real = ayuda.leer_trayectoria_real()
    real = real[real.tiempo >= "2025-10-25"]
    tiempos = sorted(ens.valid_time.unique())[:25]  # 6 días, cada 6 h
    cuadros = []
    for t in tiempos:
        fig, ax = plt.subplots(figsize=(8, 5), facecolor="#ffffff")
        ayuda.mapa_base(ax, extension=(-81.5, -68, 14.5, 23.5))
        for _, g in ens[ens.valid_time <= t].groupby("sample"):
            ax.plot(g.lon, g.lat, color=AZUL, alpha=0.28, lw=1.1, zorder=2)
        ahora = ens[ens.valid_time == t]
        ax.scatter(ahora.lon, ahora.lat, s=10, color=AZUL, zorder=3)
        r = real[real.tiempo <= t]
        ax.plot(r.lon, r.lat, color=ROJO, lw=3.2, zorder=4)
        ax.text(0.02, 0.96, f"{t:%d-oct %H:%M} UTC", transform=ax.transAxes, va="top", fontsize=15,
                bbox=dict(boxstyle="round,pad=0.4", fc="white", ec=NEGRO, lw=1.5))
        ax.text(0.98, 0.04, "azul: 50 escenarios de Weather Lab (emitidos 25-oct)\nrojo: trayectoria real (NHC)",
                transform=ax.transAxes, ha="right", fontsize=10, color=NEGRO)
        ax.set_xticks([]); ax.set_yticks([])
        fig.tight_layout(pad=0.2)
        cuadros.append(a_imagen(fig))
    guardar_gif(cuadros, "melissa_animado", ms=220, pausa_final=2500)


def radar():
    c = ayuda.copia_sentinel()
    a, d = c["db_antes"], c["db_despues"]
    nueva = (d < -18) & ~(a < -18)
    vistas = [("17 de octubre: antes", a, None), ("29 de octubre: después", d, None),
              ("Agua nueva (umbral −18 dB)", d, nueva)]
    cuadros = []
    for titulo, img, capa in vistas:
        fig, ax = plt.subplots(figsize=(6, 6), facecolor="#ffffff")
        ax.imshow(img, cmap="gray", vmin=-25, vmax=0)
        if capa is not None:
            ax.imshow(np.ma.masked_where(~capa, capa), cmap=matplotlib.colors.ListedColormap([CELESTE]))
        ax.set_title(titulo, fontsize=16, loc="left")
        ax.axis("off")
        fig.tight_layout(pad=0.3)
        cuadros.append(a_imagen(fig))
    # antes ↔ después dos veces, luego el resultado
    secuencia = [cuadros[0], cuadros[1], cuadros[0], cuadros[1], cuadros[2]]
    dur = [900, 900, 900, 900, 2600]
    pal = [x.quantize(colors=128, method=Image.Quantize.MEDIANCUT) for x in secuencia]
    pal[0].save(OUT / "radar_parpadeo.gif", save_all=True, append_images=pal[1:], duration=dur, loop=0, optimize=True)
    print("radar_parpadeo", (OUT / "radar_parpadeo.gif").stat().st_size // 1024, "KB")


def alphaearth_serie(nombre):
    s = np.load(RAIZ / "data" / "alphaearth" / f"{nombre}_serie.npz")
    anios = sorted(int(k[1:]) for k in s.files if k.startswith("a"))
    deq = lambda q: np.where(q == -128, np.nan, np.sign(q) * (q.astype("float32") / 127.5) ** 2)  # noqa: E731
    capas = {y: deq(s[f"a{y}"]) for y in anios}
    # una sola proyección para todos los años, así los colores son comparables
    c, h, w = capas[anios[0]].shape
    pila = np.concatenate([np.nan_to_num(capas[y].reshape(c, -1).T) for y in anios])
    media = pila.mean(0)
    _, _, vt = np.linalg.svd((pila - media)[:: max(1, len(pila) // 30000)], full_matrices=False)
    proy = (pila - media) @ vt[:3].T
    lo, hi = np.percentile(proy, 2, axis=0), np.percentile(proy, 98, axis=0)
    base = capas[anios[0]]
    cuadros = []
    for i, y in enumerate(anios):
        rgb = np.clip((proy[i * h * w:(i + 1) * h * w] - lo) / (hi - lo), 0, 1).reshape(h, w, 3)
        e = capas[y]
        cambio = 1 - np.nansum(base * e, 0) / (np.sqrt(np.nansum(base ** 2, 0)) * np.sqrt(np.nansum(e ** 2, 0)))
        fig, ax = plt.subplots(1, 2, figsize=(10, 5.2), facecolor="#ffffff")
        ax[0].imshow(rgb); ax[0].set_title(f"AlphaEarth {y}", loc="left", fontsize=16)
        ax[1].imshow(cambio, cmap="magma", vmin=0, vmax=0.5); ax[1].set_title(f"Cambio desde {anios[0]}", loc="left", fontsize=16)
        for a in ax:
            a.axis("off")
        fig.tight_layout(pad=1.6)
        cuadros.append(a_imagen(fig))
    guardar_gif(cuadros, f"alphaearth_{nombre}", ms=700, pausa_final=2500)


if __name__ == "__main__":
    for arg in sys.argv[1:]:
        f, _, p = arg.partition(":")
        globals()[f](*([p] if p else []))
