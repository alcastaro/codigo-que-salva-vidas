"""Funciones de apoyo del taller «Código que Salva Vidas» (DevFest Santo Domingo 2026).

Este archivo esconde la parte aburrida (descargas, reproyecciones, mosaicos) para que
las celdas del notebook se lean como la historia que cuentan. Si quieres ver cómo se
hace algo, todo está aquí y comentado.

Fuentes y licencias en el README del repositorio.
"""
from __future__ import annotations

import json
import math
import os
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

REPO_RAW = os.environ.get(
    "TALLER_RAW", "https://raw.githubusercontent.com/alcastaro/codigo-que-salva-vidas/main"
)
CACHE = Path(os.environ.get("TALLER_CACHE", "datos_taller"))

# Lugares de ejemplo. (lat, lon) en grados decimales.
LUGARES = {
    "Black River, Jamaica": (18.026, -77.850),
    "Kingston, Jamaica": (17.997, -76.794),
    "Santo Domingo, RD": (18.486, -69.931),
    "Santiago, RD": (19.451, -70.697),
    "Puerto Príncipe, Haití": (18.594, -72.307),
}


# ----------------------------------------------------------------------------- datos
def dato(ruta: str) -> Path:
    """Devuelve un archivo del repo. Si no está en local, lo baja de GitHub una vez."""
    local_repo = Path(__file__).resolve().parents[1] / ruta
    if local_repo.exists():
        return local_repo
    destino = CACHE / ruta
    if not destino.exists():
        destino.parent.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(f"{REPO_RAW}/{ruta}", destino)
    return destino


def distancia_km(lat1, lon1, lat2, lon2):
    """Distancia sobre la esfera (fórmula del haversine)."""
    r = 6371.0
    p1, p2 = np.radians(lat1), np.radians(lat2)
    dp, dl = p2 - p1, np.radians(np.asarray(lon2) - lon1)
    a = np.sin(dp / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(dl / 2) ** 2
    return 2 * r * np.arcsin(np.sqrt(a))


def mapa_base(ax, extension=(-82, -66, 14, 24)):
    """Dibuja los contornos de países del Caribe (Natural Earth, dominio público)."""
    geo = json.loads(dato("data/caribe_paises.geojson").read_text())
    for f in geo["features"]:
        g = f["geometry"]
        polys = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
        for poly in polys:
            x, y = zip(*poly[0])
            ax.fill(x, y, color="#ffffff", ec="#1e1e1e", lw=0.8, zorder=1)
    ax.set_facecolor("#c3ecf6")
    ax.set_xlim(extension[0], extension[1])
    ax.set_ylim(extension[2], extension[3])
    ax.set_aspect("equal")


# ------------------------------------------------------------------ Weather Lab (DeepMind)
def leer_weatherlab(ruta: str, tormenta: str = "AL132025") -> pd.DataFrame:
    """CSV de Weather Lab: una fila por escenario (sample) y por paso de 6 h."""
    df = pd.read_csv(dato(ruta), comment="#")
    df = df[df.track_id == tormenta].copy()
    df["valid_time"] = pd.to_datetime(df.valid_time)
    return df


def leer_trayectoria_real(ruta: str = "data/melissa/nhc_besttrack_AL132025.dat") -> pd.DataFrame:
    """Best track del NHC en formato ATCF: la trayectoria que la tormenta hizo de verdad."""
    filas = []
    for linea in dato(ruta).read_text().splitlines():
        c = [x.strip() for x in linea.split(",")]
        if len(c) < 12 or c[11] not in ("34", "0", ""):
            continue
        lat = int(c[6][:-1]) / 10 * (1 if c[6].endswith("N") else -1)
        lon = int(c[7][:-1]) / 10 * (-1 if c[7].endswith("W") else 1)
        filas.append({"tiempo": pd.to_datetime(c[2], format="%Y%m%d%H"), "lat": lat, "lon": lon,
                      "viento_kt": int(c[8]), "tipo": c[10]})
    return pd.DataFrame(filas).drop_duplicates("tiempo").reset_index(drop=True)


def categoria(kt: float) -> str:
    """Escala Saffir-Simpson a partir del viento sostenido en nudos."""
    for umbral, nombre in [(137, "Cat 5"), (113, "Cat 4"), (96, "Cat 3"), (83, "Cat 2"), (64, "Cat 1"), (34, "Tormenta tropical")]:
        if kt >= umbral:
            return nombre
    return "Depresión"


def probabilidad_paso(ens: pd.DataFrame, lat: float, lon: float, radio_km: float = 100) -> dict:
    """Qué fracción de los escenarios pasa a menos de `radio_km` del lugar, y con qué viento."""
    ens = ens[ens["sample"] >= 0].copy()
    ens["dist"] = distancia_km(lat, lon, ens.lat.values, ens.lon.values)
    cerca = ens[ens.dist <= radio_km]
    n = ens["sample"].nunique()
    pasan = cerca["sample"].nunique()
    vientos = cerca.groupby("sample").maximum_sustained_wind_speed_knots.max()
    return {
        "escenarios": n,
        "pasan_cerca": pasan,
        "probabilidad": pasan / n if n else 0.0,
        "viento_mediano_kt": float(vientos.median()) if pasan else None,
        "prob_cat5": float((vientos >= 137).sum() / n) if n else 0.0,
        "llegada_mas_probable": cerca.groupby("sample").valid_time.min().median() if pasan else None,
    }


# ------------------------------------------------------------------------ Flood Hub
def leer_floodhub() -> dict[str, pd.DataFrame]:
    """Copia guardada de la Flood Forecasting API (Flood Hub) durante Melissa."""
    def cargar(nombre):
        p = dato(f"data/floodhub/{nombre}")
        return json.loads(p.read_text())
    gauges = pd.json_normalize(cargar("gauges.json"))
    estado = pd.json_normalize(cargar("status_melissa.json"))
    return {"medidores": gauges, "estado": estado, "meta": cargar("meta.json")}


# --------------------------------------------------------------------- Sentinel (STAC)
EARTH_SEARCH = "https://earth-search.aws.element84.com/v1"
PLANETARY = "https://planetarycomputer.microsoft.com/api/stac/v1"


def caja(lat: float, lon: float, km: float = 10.0) -> tuple:
    """Caja (oeste, sur, este, norte) de `km` de lado centrada en el punto."""
    dlat = km / 2 / 111.32
    dlon = km / 2 / (111.32 * math.cos(math.radians(lat)))
    return (lon - dlon, lat - dlat, lon + dlon, lat + dlat)


def buscar_escenas(coleccion: str, bbox: tuple, fechas: str, catalogo: str = EARTH_SEARCH,
                   max_nubes: int | None = None) -> pd.DataFrame:
    """Busca escenas en un catálogo STAC y devuelve una tabla legible.

    Es una petición POST /search del estándar STAC: colección + caja + fechas.
    """
    import pystac
    import requests
    inicio, fin = fechas.split("/")
    cuerpo = {"collections": [coleccion], "bbox": list(bbox), "limit": 100,
              "datetime": f"{inicio}T00:00:00Z/{fin}T23:59:59Z"}
    if max_nubes is not None:
        cuerpo["query"] = {"eo:cloud_cover": {"lt": max_nubes}}
    r = requests.post(f"{catalogo}/search", json=cuerpo, timeout=60)
    r.raise_for_status()
    items = [pystac.Item.from_dict(f) for f in r.json()["features"]]
    filas = [{
        "fecha": it.datetime.strftime("%Y-%m-%d %H:%M"),
        "nubes_%": round(it.properties.get("eo:cloud_cover", float("nan")), 1),
        "orbita": it.properties.get("sat:relative_orbit"),
        "id": it.id, "item": it,
    } for it in items]
    return pd.DataFrame(filas).sort_values("fecha").reset_index(drop=True) if filas else pd.DataFrame()


def leer_en_caja(href: str, bbox: tuple, ancho: int = 600, nodata=None, remuestreo="bilinear") -> np.ndarray:
    """Lee solo el recorte que necesitamos de un COG remoto, ya en lat/lon."""
    import rasterio
    from rasterio.enums import Resampling
    from rasterio.transform import from_bounds
    from rasterio.vrt import WarpedVRT
    alto = int(round(ancho * (bbox[3] - bbox[1]) / (bbox[2] - bbox[0]) / math.cos(math.radians((bbox[1] + bbox[3]) / 2))))
    with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR", GDAL_HTTP_MERGE_CONSECUTIVE_RANGES="YES",
                      GDAL_HTTP_MULTIPLEX="YES", GDAL_HTTP_VERSION="2"):
        with rasterio.open(href) as src:
            kw = dict(crs="EPSG:4326", transform=from_bounds(*bbox, ancho, alto), width=ancho, height=alto,
                      resampling=getattr(Resampling, remuestreo))
            if nodata is not None:
                kw["nodata"] = nodata
            elif src.nodata is not None:
                kw["nodata"] = src.nodata
            with WarpedVRT(src, **kw) as vrt:
                return vrt.read()


def mosaico(items, banda: str, bbox: tuple, ancho: int = 600) -> np.ndarray:
    """Une varias escenas del mismo día (por ejemplo, dos tiles de Sentinel-2) en una imagen."""
    salida = None
    for it in items:
        a = leer_en_caja(it.assets[banda].href, bbox, ancho, nodata=0)[0].astype("float32")
        a[a == 0] = np.nan
        salida = a if salida is None else np.where(np.isnan(salida), a, salida)
    return salida


def una_por_tile(items) -> list:
    """Si un tile tiene dos escenas el mismo día, se queda con la de menos nubes."""
    mejor = {}
    for it in items:
        tile = it.properties.get("grid:code") or it.id.split("_")[1]
        if tile not in mejor or it.properties["eo:cloud_cover"] < mejor[tile].properties["eo:cloud_cover"]:
            mejor[tile] = it
    return sorted(mejor.values(), key=lambda it: it.properties["eo:cloud_cover"])


def sentinel2(items, bbox, ancho=600) -> dict:
    """Lee una vez las bandas roja, verde, azul e infrarroja, y calcula color real y NDVI.

    El NDVI mide qué tan verde está la vegetación: cerca de 1 = sana, cerca de 0 = suelo o daño.
    """
    items = una_por_tile(items)
    b = {x: mosaico(items, x, bbox, ancho) for x in ("red", "green", "blue", "nir")}
    return {
        "rgb": np.clip(np.dstack([b["red"], b["green"], b["blue"]]) / 3000, 0, 1),
        "ndvi": (b["nir"] - b["red"]) / (b["nir"] + b["red"] + 1e-6),
    }


def radar_db(item, bbox, ancho=600) -> np.ndarray:
    """Retrodispersión VV de Sentinel-1 en decibelios. El agua quieta sale muy oscura."""
    import planetary_computer
    from scipy.ndimage import median_filter
    href = planetary_computer.sign(item.assets["vv"].href)
    a = leer_en_caja(href, bbox, ancho)[0].astype("float32")
    a[a <= 0] = np.nan
    return median_filter(10 * np.log10(a), size=3)  # filtro de mediana: quita el "granulado" del radar


def redimensionar(mascara: np.ndarray, forma: tuple) -> np.ndarray:
    """Cambia el tamaño de una máscara por vecino más cercano (para cruzar capas de distinta resolución)."""
    filas = (np.arange(forma[0]) * mascara.shape[0] / forma[0]).astype(int)
    cols = (np.arange(forma[1]) * mascara.shape[1] / forma[1]).astype(int)
    return mascara[np.ix_(filas, cols)]


def cerca_de(mascara: np.ndarray, bbox: tuple, metros: float) -> np.ndarray:
    """Marca todo lo que queda a menos de `metros` de la máscara (dilatación)."""
    from scipy.ndimage import binary_dilation
    lado_m = math.sqrt(km2_por_pixel(bbox, mascara.shape)) * 1000
    pasos = max(1, int(round(metros / lado_m)))
    yy, xx = np.ogrid[-pasos:pasos + 1, -pasos:pasos + 1]
    return binary_dilation(mascara, structure=(xx ** 2 + yy ** 2) <= pasos ** 2)


def km2_por_pixel(bbox, forma) -> float:
    lat = (bbox[1] + bbox[3]) / 2
    alto_km = (bbox[3] - bbox[1]) * 111.32
    ancho_km = (bbox[2] - bbox[0]) * 111.32 * math.cos(math.radians(lat))
    return (alto_km / forma[0]) * (ancho_km / forma[1])


def copia_sentinel(ruta: str = "data/sentinel/black_river.npz") -> dict:
    """Lo mismo que leen las celdas en vivo, guardado de antemano por si la red va lenta."""
    c = np.load(dato(ruta))
    i8 = lambda x, k=1: np.where(x == -128, np.nan, x.astype("float32") / k)  # noqa: E731
    return {
        "rgb_antes": c["rgb_antes"] / 255, "rgb_despues": c["rgb_despues"] / 255,
        "ndvi_antes": i8(c["ndvi_antes"], 100), "ndvi_despues": i8(c["ndvi_despues"], 100),
        "db_antes": i8(c["db_antes"]), "db_despues": i8(c["db_despues"]),
    }


# ------------------------------------------------------------------- AlphaEarth (AEF)
def _indice_aef() -> pd.DataFrame:
    return pd.read_parquet(dato("data/aef_index_ligero.parquet"))


def embeddings_alphaearth(bbox: tuple, anio: int, ancho: int = 400) -> np.ndarray:
    """Embeddings anuales de AlphaEarth (64 números por píxel) desde Source Cooperative.

    Se guardan como enteros de 8 bits; se recuperan con (v/127,5)² × signo(v).
    -128 significa «sin dato». Devuelve un arreglo (64, alto, ancho).
    """
    idx = _indice_aef()
    lon, lat = (bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2
    fila = idx[(idx.year == anio) & (idx.wgs84_west <= lon) & (idx.wgs84_east >= lon)
               & (idx.wgs84_south <= lat) & (idx.wgs84_north >= lat)]
    if fila.empty:
        raise ValueError(f"No hay embeddings de {anio} para ese lugar.")
    crudo = leer_en_caja("/vsicurl/" + fila.path.iloc[0], bbox, ancho, nodata=-128, remuestreo="nearest")
    x = crudo.astype("float32")
    x = np.sign(x) * (x / 127.5) ** 2
    x[crudo == -128] = np.nan
    return x


def guardar_embeddings(emb: np.ndarray, ruta: str) -> None:
    q = np.where(np.isnan(emb), -128, np.sign(emb) * np.sqrt(np.abs(emb)) * 127.5)
    np.savez_compressed(ruta, q=np.clip(np.round(q), -128, 127).astype("int8"))


def cargar_embeddings(ruta: str) -> np.ndarray:
    q = np.load(dato(ruta))["q"]
    x = q.astype("float32")
    x = np.sign(x) * (x / 127.5) ** 2
    x[q == -128] = np.nan
    return x


def similitud(emb: np.ndarray, vector: np.ndarray) -> np.ndarray:
    """Similitud coseno de cada píxel con un vector de referencia (1 = idéntico)."""
    n = np.sqrt(np.nansum(emb ** 2, axis=0)) * np.linalg.norm(vector)
    return np.einsum("chw,c->hw", np.nan_to_num(emb), vector) / np.where(n == 0, np.nan, n)


def vector_en(emb: np.ndarray, bbox: tuple, lat: float, lon: float, radio_px: int = 2) -> np.ndarray:
    """Promedio de los embeddings alrededor de un punto: «esto es lo que busco»."""
    _, h, w = emb.shape
    fila = int((bbox[3] - lat) / (bbox[3] - bbox[1]) * h)
    col = int((lon - bbox[0]) / (bbox[2] - bbox[0]) * w)
    v = emb[:, max(fila - radio_px, 0):fila + radio_px + 1, max(col - radio_px, 0):col + radio_px + 1]
    return np.nanmean(v.reshape(64, -1), axis=1)


def rgb_embeddings(emb: np.ndarray) -> np.ndarray:
    """Tres componentes principales de los 64 números, como colores: zonas parecidas, color parecido."""
    c, h, w = emb.shape
    x = np.nan_to_num(emb.reshape(c, -1).T)
    x = x - x.mean(0)
    _, _, vt = np.linalg.svd(x[:: max(1, len(x) // 20000)], full_matrices=False)
    p = x @ vt[:3].T
    lo, hi = np.percentile(p, 2, axis=0), np.percentile(p, 98, axis=0)
    return np.clip((p - lo) / (hi - lo), 0, 1).reshape(h, w, 3)


# --------------------------------------------------------------------------- Gemini
def cliente_gemini():
    """Cliente de la API de Gemini con la key guardada en los secretos de Colab."""
    from google import genai
    try:
        from google.colab import userdata
        key = userdata.get("GOOGLE_API_KEY")
    except Exception:
        key = os.environ.get("GOOGLE_API_KEY")
    return genai.Client(api_key=key)


def elegir_modelo(cliente, familia: str = "flash") -> str:
    """Elige el modelo más reciente de una familia ('flash', 'pro' o 'gemma') disponible para tu key."""
    nombres = [m.name.split("/")[-1] for m in cliente.models.list()
               if "generateContent" in (m.supported_actions or [])]
    candidatos = [n for n in nombres if familia in n and "preview" not in n and "tts" not in n
                  and "image" not in n and "live" not in n and "lite" not in n]
    if not candidatos:
        candidatos = [n for n in nombres if familia in n]
    return sorted(candidatos)[-1] if candidatos else "gemini-2.5-flash"


INSTRUCCION_ALERTA = """Eres el redactor de alertas de una oficina de protección civil del Caribe.
Recibes datos técnicos y escribes UNA alerta para la población, en español sencillo.
Reglas:
- Se tiene que entender en 3 segundos: primero QUÉ pasa, luego DÓNDE, luego QUÉ HACER.
- Máximo 280 caracteres en el campo 'mensaje'. Sin tecnicismos (nada de nudos, hPa, NDVI ni dB).
- No inventes datos que no estén en la entrada. Si la certeza es baja, dilo.
- Incluye los campos del Protocolo Común de Alertas (CAP): severidad, urgencia y certeza.
"""


def redactar_alerta(cliente, modelo: str, datos_tecnicos: dict) -> dict:
    """Pide a Gemini (o Gemma) una alerta estructurada a partir de los números del notebook."""
    from google.genai import types
    esquema = {
        "type": "object",
        "properties": {
            "titulo": {"type": "string"},
            "mensaje": {"type": "string"},
            "que_hacer": {"type": "array", "items": {"type": "string"}},
            "severidad": {"type": "string", "enum": ["Extreme", "Severe", "Moderate", "Minor", "Unknown"]},
            "urgencia": {"type": "string", "enum": ["Immediate", "Expected", "Future", "Past", "Unknown"]},
            "certeza": {"type": "string", "enum": ["Observed", "Likely", "Possible", "Unlikely", "Unknown"]},
        },
        "required": ["titulo", "mensaje", "que_hacer", "severidad", "urgencia", "certeza"],
    }
    contenido = "Datos técnicos:\n" + json.dumps(datos_tecnicos, ensure_ascii=False, default=str, indent=1)
    if "gemma" in modelo:  # Gemma no admite instrucción de sistema ni esquema: va todo en el texto
        r = cliente.models.generate_content(
            model=modelo,
            contents=INSTRUCCION_ALERTA + "\nResponde SOLO con un JSON con las claves "
            + ", ".join(esquema["required"]) + ".\n\n" + contenido)
        texto = r.text.strip().removeprefix("```json").removeprefix("```").removesuffix("```")
        return json.loads(texto)
    r = cliente.models.generate_content(
        model=modelo, contents=contenido,
        config=types.GenerateContentConfig(system_instruction=INSTRUCCION_ALERTA,
                                           response_mime_type="application/json",
                                           response_schema=esquema, temperature=0.2))
    return json.loads(r.text)


def mostrar_alerta(a: dict) -> None:
    """Pinta la alerta como la vería alguien en su teléfono."""
    from IPython.display import HTML, display
    colores = {"Extreme": "#ea4335", "Severe": "#f9ab00", "Moderate": "#4285f4", "Minor": "#34a853"}
    c = colores.get(a.get("severidad"), "#1e1e1e")
    pasos = "".join(f"<li>{p}</li>" for p in a.get("que_hacer", []))
    display(HTML(f"""
    <div style="max-width:380px;border:2px solid #1e1e1e;border-radius:28px;padding:20px 24px;
                font-family:'Google Sans',system-ui,sans-serif;background:#fff;color:#1e1e1e">
      <div style="display:inline-block;background:{c};color:#fff;border-radius:999px;padding:4px 14px;
                  font-size:13px">{a.get('severidad')} · {a.get('urgencia')} · {a.get('certeza')}</div>
      <h3 style="margin:12px 0 6px">{a.get('titulo')}</h3>
      <p style="font-size:16px;margin:0 0 8px">{a.get('mensaje')}</p>
      <ul style="margin:0;padding-left:20px">{pasos}</ul>
    </div>"""))
