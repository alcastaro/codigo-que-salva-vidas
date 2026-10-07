"""Figuras del deck con la paleta del DevFest (fondo off-white, contornos Black 02).

    .venv/bin/python tools/figuras_deck.py
"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import qrcode
from qrcode.image.svg import SvgPathImage  # noqa: F401  (disponible si se prefiere SVG)

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "taller"))
import ayuda  # noqa: E402

OUT = RAIZ / "deck" / "figuras"
OUT.mkdir(parents=True, exist_ok=True)
NEGRO, BLANCO, OFF = "#1e1e1e", "#ffffff", "#f0f0f0"
AZUL, VERDE, AMARILLO, ROJO = "#4285f4", "#34a853", "#f9ab00", "#ea4335"
PORTAL = "https://alcastaro.github.io/codigo-que-salva-vidas/"


def estilo(ax):
    for s in ax.spines.values():
        s.set_color(NEGRO); s.set_linewidth(2)
    ax.set_xticks([]); ax.set_yticks([])


def huracan():
    ens = ayuda.leer_weatherlab("data/melissa/weatherlab_FNV3P2_ensemble_2025_10_25T00.csv")
    real = ayuda.leer_trayectoria_real()
    real = real[real.tiempo >= "2025-10-21"]
    fig, ax = plt.subplots(figsize=(8.8, 5.4), facecolor=BLANCO)
    ayuda.mapa_base(ax, extension=(-81.5, -68, 14.5, 23.5))
    for _, t in ens.groupby("sample"):
        ax.plot(t.lon, t.lat, color=AZUL, alpha=0.28, lw=1.1, zorder=2)
    ax.plot(real.lon, real.lat, color=ROJO, lw=3.5, zorder=3)
    p = real.loc[real.viento_kt.idxmax()]
    ax.scatter(p.lon, p.lat, s=160, color=AMARILLO, ec=NEGRO, lw=2, zorder=4)
    estilo(ax)
    fig.savefig(OUT / "melissa_ensamble.png", dpi=200, bbox_inches="tight", pad_inches=0)
    plt.close(fig)


def alphaearth():
    bbox = ayuda.caja(18.04, -77.82, 10)
    emb = ayuda.cargar_embeddings("data/alphaearth/black_river_2024.npz")
    sim = ayuda.similitud(emb, ayuda.vector_en(emb, bbox, 18.033, -77.858, 1))
    fig, ax = plt.subplots(1, 2, figsize=(10, 5), facecolor=BLANCO)
    ax[0].imshow(ayuda.rgb_embeddings(emb))
    ax[1].imshow(np.ma.masked_where(~(sim > 0.9), sim > 0.9), cmap=matplotlib.colors.ListedColormap([ROJO]))
    ax[1].imshow(ayuda.rgb_embeddings(emb), alpha=0.35)
    for a in ax:
        estilo(a)
    fig.tight_layout(pad=0.3)
    fig.savefig(OUT / "alphaearth_similitud.png", dpi=200, bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)
    # Versión cuadrada para la tarjeta con foto: huella de AlphaEarth + en rojo lo «parecido al pueblo».
    fig = plt.figure(figsize=(6, 6.55), dpi=200)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.imshow(ayuda.rgb_embeddings(emb), aspect="auto")
    ax.imshow(np.ma.masked_where(~(sim > 0.9), sim > 0.9), cmap=matplotlib.colors.ListedColormap([ROJO]), aspect="auto")
    ax.axis("off")
    fig.savefig(OUT / "alphaearth_cuadro.png")
    plt.close(fig)


def radar():
    bbox = ayuda.caja(18.04, -77.82, 10)
    s1 = ayuda.buscar_escenas("sentinel-1-rtc", bbox, "2025-10-16/2025-10-30", catalogo=ayuda.PLANETARY)
    a = ayuda.radar_db(s1[s1.fecha.str.startswith("2025-10-17")].item.iloc[0], bbox)
    d = ayuda.radar_db(s1[s1.fecha.str.startswith("2025-10-29")].item.iloc[0], bbox)
    nueva = (d < -18) & ~(a < -18)
    fig, ax = plt.subplots(1, 2, figsize=(10, 5), facecolor=BLANCO)
    ax[0].imshow(a, cmap="gray", vmin=-25, vmax=0)
    ax[1].imshow(d, cmap="gray", vmin=-25, vmax=0)
    ax[1].imshow(np.ma.masked_where(~nueva, nueva), cmap=matplotlib.colors.ListedColormap(["#57caff"]))
    for x in ax:
        estilo(x)
    fig.tight_layout(pad=0.3)
    fig.savefig(OUT / "radar_agua_nueva.png", dpi=200, bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)


def radar_cuadro():
    """Radar del 29-oct con el agua nueva resaltada, desde la copia guardada de la Pista B."""
    c = np.load(RAIZ / "data" / "sentinel" / "black_river.npz")
    a, d = c["db_antes"].astype(float), c["db_despues"].astype(float)
    nueva = (d < -18) & ~(a < -18) & (d > -128)
    fig = plt.figure(figsize=(6, 6.55), dpi=200)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.imshow(np.where(d == -128, np.nan, d), cmap="gray", vmin=-25, vmax=0, aspect="auto")
    ax.imshow(np.ma.masked_where(~nueva, nueva), cmap=matplotlib.colors.ListedColormap(["#57caff"]), aspect="auto")
    ax.axis("off")
    fig.savefig(OUT / "radar_cuadro.png")
    plt.close(fig)


def qr():
    q = qrcode.QRCode(border=1, box_size=20, error_correction=qrcode.constants.ERROR_CORRECT_M)
    q.add_data(PORTAL)
    q.make(fit=True)
    q.make_image(fill_color=NEGRO, back_color=BLANCO).save(OUT / "qr_portal.png")


if __name__ == "__main__":
    for f in sys.argv[1:] or ["huracan", "alphaearth", "qr", "radar"]:
        globals()[f]()
        print("ok", f)
