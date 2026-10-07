"""Genera los notebooks del taller a partir de este archivo (fuente única).

    .venv/bin/python tools/construir_notebooks.py
"""
from pathlib import Path

import nbformat as nbf

RAIZ = Path(__file__).resolve().parents[1]
REPO = "alcastaro/codigo-que-salva-vidas"
COLAB = f"https://colab.research.google.com/github/{REPO}/blob/main/taller"

INSTALAR = f"""# Instala lo que falta en Colab y trae las funciones de apoyo del taller (~30 s)
!pip -q install rasterio pystac-client planetary-computer google-genai
!wget -q -N https://raw.githubusercontent.com/{REPO}/main/taller/ayuda.py
import ayuda, numpy as np, pandas as pd, matplotlib.pyplot as plt
plt.rcParams.update({{"figure.dpi": 110, "font.size": 10}})
print("Listo ✅")"""

KEY_MD = """### 🔑 Tu API key de Gemini (2 minutos, solo la primera vez)
1. Abre **[aistudio.google.com/apikey](https://aistudio.google.com/apikey)** y pulsa **Create API key**. Es gratis.
2. En Colab, abre el panel de la **llave 🔑 (Secretos)** a la izquierda.
3. Pulsa **Add new secret**: nombre `GOOGLE_API_KEY`, valor tu key, y activa **Notebook access**.

> Atajo: en ese mismo panel, **Gemini API keys → Import key from Google AI Studio** lo hace por ti.
>
> **Nunca pegues una key dentro de una celda.** Si compartes el notebook o lo subes a GitHub, la key viaja con él."""


def md(t):
    return nbf.v4.new_markdown_cell(t)


def code(t):
    return nbf.v4.new_code_cell(t)


def notebook(celdas, nombre):
    nb = nbf.v4.new_notebook()
    nb.metadata = {"colab": {"provenance": [], "toc_visible": True},
                   "kernelspec": {"name": "python3", "display_name": "Python 3"},
                   "language_info": {"name": "python"}}
    nb.cells = celdas
    ruta = RAIZ / "taller" / nombre
    nbf.write(nb, ruta)
    print("escrito", ruta.relative_to(RAIZ))


# ============================================================================ PISTA A
pista_a = [
    md(f"""# 🌀 Pista A — El huracán: de 50 futuros posibles a una alerta
**Código que Salva Vidas · DevFest Santo Domingo 2026 · Taller · Nivel principiante**

[![Abrir en Colab](https://colab.research.google.com/assets/colab-badge.svg)]({COLAB}/pista_A_huracan.ipynb)

El 28 de octubre de 2025, **Melissa** tocó tierra en Jamaica como huracán categoría 5, con vientos de 160 nudos (unos 300 km/h). Fue el más fuerte que ha golpeado la isla.
Según Google DeepMind, su modelo **WeatherNext** anticipó esa llegada como categoría 5 **cinco días antes, con un 80 % de confianza**.

En esta pista haces tú lo que hicieron los pronosticadores:

| Paso | Qué haces | Producto de Google |
|---|---|---|
| 1 | Ver los **50 escenarios** que el modelo de IA dibujó tres días antes | Weather Lab (DeepMind) |
| 2 | Calcular la **probabilidad** de que el ojo pase cerca de un lugar | Weather Lab |
| 3 | Ver qué **ríos** marcaban peligro de inundación | Flood Hub |
| 4 | Convertir todo en una **alerta** que se entienda en 3 segundos | Gemini (AI Studio) |

**No necesitas saber programar.** Ejecuta cada celda con ▶️ (o `Shift + Enter`) en orden y lee el texto de arriba."""),
    code(INSTALAR),
    md("""## Paso 1 · 50 futuros posibles

Un pronóstico moderno no dibuja **una** trayectoria: dibuja **muchas**. Cada una es un futuro posible, y a ese conjunto se le llama **ensamble**.
Si todas las líneas van juntas, el modelo está seguro. Si se abren como un abanico, hay incertidumbre.

Vamos a cargar el pronóstico que el modelo experimental de ciclones de DeepMind emitió el **25 de octubre de 2025 a las 00:00 UTC**, tres días antes de la llegada a tierra.
Lo comparamos con la **trayectoria real**, publicada después por el Centro Nacional de Huracanes de EE. UU. (NHC)."""),
    code("""# @title Elige la fecha en que se emitió el pronóstico { run: "auto" }
emision = "2025_10_25T00"  # @param ["2025_10_22T00", "2025_10_25T00", "2025_10_27T00"]

ens = ayuda.leer_weatherlab(f"data/melissa/weatherlab_FNV3P2_ensemble_{emision}.csv")
real = ayuda.leer_trayectoria_real()
print(f"{ens['sample'].nunique()} escenarios · {len(ens)} puntos (uno cada 6 horas por escenario)")
ens.head()"""),
    code("""fig, ax = plt.subplots(figsize=(9, 6))
ayuda.mapa_base(ax)
for _, t in ens.groupby("sample"):
    ax.plot(t.lon, t.lat, color="#4285f4", alpha=0.25, lw=1, zorder=2)
ax.plot(real.lon, real.lat, color="#ea4335", lw=3, zorder=3, label="Trayectoria real (NHC)")
ax.plot([], [], color="#4285f4", label="Los 50 escenarios del modelo")
llegada = real.loc[real.viento_kt.idxmax()]
ax.scatter(llegada.lon, llegada.lat, s=120, color="#f9ab00", ec="#1e1e1e", zorder=4,
           label=f"Máximo: {llegada.viento_kt} nudos ({ayuda.categoria(llegada.viento_kt)})")
ax.set_title(f"Melissa · pronóstico emitido el {emision[:10].replace('_', '-')}")
ax.legend(loc="lower left"); plt.show()"""),
    md("""**🧠 Para pensar:** ¿el abanico azul contiene la línea roja? Cambia la fecha de emisión arriba (22, 25 o 27 de octubre) y vuelve a ejecutar.
¿Cómo cambia el abanico a medida que se acerca la tormenta?

## Paso 2 · ¿Qué tan probable es que me toque?

Con 50 escenarios, la probabilidad se calcula **contando**: si 40 de 50 pasan a menos de 100 km de un lugar, la probabilidad es del 80 %.
Elige un lugar en el desplegable o escribe tus propias coordenadas."""),
    code("""# @title Elige un lugar { run: "auto" }
lugar = "Black River, Jamaica"  # @param ["Black River, Jamaica", "Kingston, Jamaica", "Santo Domingo, RD", "Santiago, RD", "Puerto Príncipe, Haití"]
radio_km = 100  # @param {type:"slider", min:25, max:300, step:25}

lat, lon = ayuda.LUGARES[lugar]
p = ayuda.probabilidad_paso(ens, lat, lon, radio_km)
print(f"📍 {lugar}")
print(f"   {p['pasan_cerca']} de {p['escenarios']} escenarios pasan a menos de {radio_km} km → probabilidad {p['probabilidad']:.0%}")
if p["pasan_cerca"]:
    print(f"   Viento máximo típico al pasar: {p['viento_mediano_kt']:.0f} nudos ({ayuda.categoria(p['viento_mediano_kt'])})")
    print(f"   Probabilidad de que llegue como categoría 5: {p['prob_cat5']:.0%}")
    print(f"   Momento más probable: {p['llegada_mas_probable']:%d-%b %H:%M} UTC")"""),
    md("""## Paso 3 · ¿Qué ríos se van a desbordar? (Flood Hub)

**Flood Hub** pronostica crecidas de ríos hasta 7 días antes en más de 150 países, incluso en ríos **sin estaciones de medición**.
Lo logra con un modelo de IA (dos redes neuronales LSTM en cadena) entrenado con datos de miles de ríos de todo el mundo.

La API de Flood Hub requiere una key aprobada, así que el facilitador del taller extrajo una **copia** de lo que marcaba durante Melissa.
Para verlo en vivo, abre [sites.research.google/floods](https://sites.research.google/floods)."""),
    code("""try:
    fh = ayuda.leer_floodhub()
    est = fh["estado"]
    print("Extraído:", fh["meta"]["extraido"], "· estado a", fh["meta"]["melissa_cutoff"])
    print(f"{len(fh['medidores'])} puntos de pronóstico en {', '.join(fh['meta']['regiones'])}")
    display(est.filter(regex="gaugeId|severity|forecastTrend|issuedTime").head(15))
except Exception as e:
    print("La copia de Flood Hub aún no está disponible en este repositorio:", e)
    fh = None"""),
    code("""if fh is not None and len(fh["estado"]):
    m = fh["medidores"].merge(fh["estado"], left_on="gaugeId", right_on="gaugeId", how="left")
    col = {"EXTREME": "#ea4335", "SEVERE": "#f9ab00", "ABOVE_NORMAL": "#4285f4", "NO_FLOODING": "#34a853"}
    fig, ax = plt.subplots(figsize=(9, 6)); ayuda.mapa_base(ax)
    for sev, g in m.groupby(m.get("severity", pd.Series(["?"] * len(m))).fillna("SIN_DATO")):
        ax.scatter(g["location.longitude"], g["location.latitude"], s=25, color=col.get(sev, "#9e9e9e"),
                   ec="#1e1e1e", lw=0.4, zorder=3, label=sev)
    ax.plot(real.lon, real.lat, color="#1e1e1e", lw=1.5, ls="--", zorder=2, label="Melissa")
    ax.legend(loc="lower left", fontsize=8); ax.set_title("Flood Hub durante Melissa"); plt.show()"""),
    md(KEY_MD + """

## Paso 4 · De los números a una alerta

Un pronóstico excelente no salva a nadie si la persona no lo entiende. Le pasamos a **Gemini** los números de los pasos anteriores, y él redacta la alerta siguiendo reglas claras.
La alerta lleva además tres campos del **Protocolo Común de Alertas (CAP)**: severidad, urgencia y certeza. CAP es el estándar con el que las autoridades publican alertas, y es el formato que Google usa para mostrarlas en Búsqueda y Maps."""),
    code("""cliente = ayuda.cliente_gemini()
modelo = ayuda.elegir_modelo(cliente, "flash")
print("Modelo:", modelo)

datos = {
    "evento": "Huracán Melissa",
    "pronostico_emitido": emision,
    "lugar": lugar,
    "probabilidad_paso_a_menos_de_km": {"km": radio_km, "probabilidad": round(p["probabilidad"], 2)},
    "viento_esperado": ayuda.categoria(p["viento_mediano_kt"] or 0),
    "probabilidad_categoria_5": round(p["prob_cat5"], 2),
    "llegada_mas_probable_utc": p["llegada_mas_probable"],
    "rios_en_alerta_flood_hub": int(fh["estado"].get("severity", pd.Series()).isin(["EXTREME", "SEVERE"]).sum()) if fh else "sin datos",
}
alerta = ayuda.redactar_alerta(cliente, modelo, datos)
ayuda.mostrar_alerta(alerta)"""),
    md("""### 🧪 Extra: la misma alerta con Gemma, un modelo abierto

**Gemma** es la familia de modelos abiertos de Google. Sus versiones pequeñas corren **sin internet**, en un teléfono o una Raspberry Pi.
Así lo hizo *Acuífero·Vigía*, ganador del premio Global Resilience del Gemma 4 Good Challenge: un sistema de alerta de inundaciones que funciona sin conexión.
¿La alerta de Gemma es tan buena como la de Gemini?"""),
    code("""modelo_gemma = ayuda.elegir_modelo(cliente, "gemma")
print("Modelo:", modelo_gemma)
ayuda.mostrar_alerta(ayuda.redactar_alerta(cliente, modelo_gemma, datos))"""),
    md("""## 🏁 Retos (si te sobra tiempo)
1. Emite la alerta para **Santo Domingo** con el pronóstico del **22 de octubre**. ¿Qué certeza le pone Gemini? ¿Tiene sentido?
2. Edita `ayuda.INSTRUCCION_ALERTA` para que la alerta salga en **creole haitiano** o en **inglés jamaicano**, y vuelve a ejecutar el paso 4.
3. ¿Cuántos escenarios predijeron categoría 5 en Jamaica el 22 de octubre? ¿Y el 27?

---
**Fuentes y licencias.** Pronósticos: Google DeepMind Weather Lab, modelo experimental de ciclones, datos históricos con licencia CC BY 4.0. Es un pronóstico de investigación, no un producto oficial.
Trayectoria real: NOAA / National Hurricane Center (best track AL132025). Inundaciones: Google Flood Forecasting API (uso no comercial).
Contornos: Natural Earth. **Para alertas reales, consulta siempre a tu servicio meteorológico nacional.**"""),
]

# ============================================================================ PISTA B
pista_b = [
    md(f"""# 🛰️ Pista B — El satélite: qué pasó y a quién le pasó
**Código que Salva Vidas · DevFest Santo Domingo 2026 · Taller · Nivel principiante**

[![Abrir en Colab](https://colab.research.google.com/assets/colab-badge.svg)]({COLAB}/pista_B_satelite.ipynb)

Melissa pasó sobre **Black River**, en el suroeste de Jamaica, el 28 de octubre de 2025. En esta pista usas imágenes de satélite **gratuitas y abiertas** para responder tres preguntas:

| Paso | Pregunta | Herramienta |
|---|---|---|
| 1 | ¿Qué imágenes hay de antes y de después? | Catálogos **STAC** de Sentinel |
| 2 | ¿Qué le pasó a la vegetación? | **Sentinel-2** (óptico) |
| 3 | ¿Dónde se acumuló agua, aunque hubiera nubes? | **Sentinel-1** (radar) |
| 4 | ¿Había gente viviendo ahí? | **AlphaEarth Foundations** (Google DeepMind) |
| 5 | ¿Cómo se lo contamos a la población? | **Gemini** |

Todo esto **no requiere cuenta ni proyecto de Google Cloud**: los datos son abiertos.
Ejecuta cada celda con ▶️ en orden."""),
    code(INSTALAR),
    code("""# @title La zona de estudio { run: "auto" }
LAT, LON = 18.04, -77.82   # Black River y su humedal (Jamaica)
KM = 10                    # lado de la caja, en kilómetros
bbox = ayuda.caja(LAT, LON, KM)
print("Caja (oeste, sur, este, norte):", [round(x, 3) for x in bbox])"""),
    md("""## Paso 1 · Buscar imágenes como un profesional: STAC

**STAC** (*SpatioTemporal Asset Catalog*) es el estándar abierto para buscar imágenes de satélite: le das un lugar y unas fechas, y te devuelve las escenas disponibles.
Usamos dos catálogos públicos:
- **Earth Search** (Element 84, sobre AWS) para **Sentinel-2**: fotos ópticas de 10 m, como una cámara, con las nubes como problema.
- **Microsoft Planetary Computer** para **Sentinel-1**: radar, que **atraviesa las nubes** y funciona de noche.

Los dos satélites son del programa europeo **Copernicus**, y sus datos son libres."""),
    code("""s2 = ayuda.buscar_escenas("sentinel-2-l2a", bbox, "2025-10-15/2025-11-10", max_nubes=60)
print("Sentinel-2 (óptico):"); display(s2.drop(columns="item"))
s1 = ayuda.buscar_escenas("sentinel-1-rtc", bbox, "2025-10-10/2025-11-05", catalogo=ayuda.PLANETARY)
print("Sentinel-1 (radar):"); display(s1.drop(columns="item"))"""),
    md("""**🧠 Para pensar:** quita `max_nubes=60` y vuelve a buscar. Mira las escenas del 25 y el 28 de octubre, los días del huracán: **100 % de nubes**. Por eso necesitamos el radar.

## Paso 2 · Antes y después en color real

Elegimos una fecha de antes (**20-oct**) y otra de después (**30-oct**, dos días tras el huracán). Black River queda en el borde entre dos *tiles* (cuadrículas) de Sentinel-2, así que unimos las dos en un **mosaico**.
El **NDVI** mide qué tan verde y sana está la vegetación, usando la luz roja y el infrarrojo cercano que las plantas reflejan."""),
    code("""# @title Antes y después { run: "auto" }
EN_VIVO = False  # @param {type:"boolean"}
# EN_VIVO = True lee las imágenes ahora mismo desde AWS (30–60 s). False usa una copia idéntica guardada en GitHub.
if EN_VIVO:
    antes   = list(s2[s2.fecha.str.startswith("2025-10-20")].item)
    despues = list(s2[s2.fecha.str.startswith("2025-10-30")].item)
    A, D = ayuda.sentinel2(antes, bbox), ayuda.sentinel2(despues, bbox)
    rgb_a, rgb_d, perdida = A["rgb"], D["rgb"], A["ndvi"] - D["ndvi"]
else:
    copia = ayuda.copia_sentinel()
    rgb_a, rgb_d = copia["rgb_antes"], copia["rgb_despues"]
    perdida = copia["ndvi_antes"] - copia["ndvi_despues"]

fig, ax = plt.subplots(1, 3, figsize=(15, 5))
ax[0].imshow(rgb_a); ax[0].set_title("20 de octubre (antes)")
ax[1].imshow(rgb_d); ax[1].set_title("30 de octubre (después)")
im = ax[2].imshow(perdida, cmap="RdYlGn_r", vmin=-0.4, vmax=0.4); ax[2].set_title("Pérdida de vegetación (NDVI)")
plt.colorbar(im, ax=ax[2], shrink=0.7)
for a in ax: a.axis("off")
plt.show()"""),
    md("""## Paso 3 · El radar ve el agua a través de las nubes

El radar de Sentinel-1 lanza microondas y mide cuánto rebota. El **agua quieta** actúa como un espejo y devuelve muy poco, así que sale **oscura**.
Regla simple: si un píxel pasa de "claro" antes a "oscuro" después, ahí apareció **agua nueva**.
Comparamos dos pasadas de la **misma órbita** (17-oct y 29-oct) para que la geometría sea idéntica."""),
    code("""# @title El radar antes y después { run: "auto" }
EN_VIVO = False  # @param {type:"boolean"}
# EN_VIVO = True lee el radar desde Microsoft Planetary Computer (de 20 s a varios minutos, según la red).
if EN_VIVO:
    orbita = 150
    r_antes   = s1[(s1.orbita == orbita) & s1.fecha.str.startswith("2025-10-17")].item.iloc[0]
    r_despues = s1[(s1.orbita == orbita) & s1.fecha.str.startswith("2025-10-29")].item.iloc[0]
    db_a, db_d = ayuda.radar_db(r_antes, bbox), ayuda.radar_db(r_despues, bbox)
else:
    copia = ayuda.copia_sentinel()
    db_a, db_d = copia["db_antes"], copia["db_despues"]

UMBRAL_DB = -18   # por debajo de esto, lo tratamos como agua
agua_nueva = (db_d < UMBRAL_DB) & ~(db_a < UMBRAL_DB)
km2 = agua_nueva.sum() * ayuda.km2_por_pixel(bbox, agua_nueva.shape)

fig, ax = plt.subplots(1, 3, figsize=(15, 5))
ax[0].imshow(db_a, cmap="gray", vmin=-25, vmax=0); ax[0].set_title("Radar 17-oct")
ax[1].imshow(db_d, cmap="gray", vmin=-25, vmax=0); ax[1].set_title("Radar 29-oct")
ax[2].imshow(db_d, cmap="gray", vmin=-25, vmax=0)
ax[2].imshow(np.ma.masked_where(~agua_nueva, agua_nueva), cmap="cool", alpha=0.9)
ax[2].set_title(f"Agua nueva ≈ {km2:.1f} km²")
for a in ax: a.axis("off")
plt.show()"""),
    md("""**🧠 Para pensar:** ¿ves "agua nueva" en el **mar**? No es una inundación. Después del huracán había viento, el mar se picó, y eso cambia el rebote del radar.
Un umbral simple tiene límites. Los sistemas reales, como Flood Hub, usan modelos entrenados y máscaras de agua permanente.

## Paso 4 · ¿Qué había en el suelo? AlphaEarth Foundations

**AlphaEarth Foundations** (Google DeepMind) resume años de observaciones de satélite (óptico, radar, relieve, clima…) en **64 números por cada píxel de 10 m**. Esos 64 números son un **embedding**, una especie de "huella digital" del terreno.
Dos lugares parecidos (dos barrios, dos manglares) tienen huellas parecidas. Así se puede **buscar por similitud** sin entrenar ningún modelo.

Los embeddings anuales son abiertos en **Source Cooperative** (CC BY 4.0). Para Black River usamos una **copia** de 2024 (el año anterior al huracán), porque leer el original tarda unos minutos.
Al final puedes probar con tu propio lugar."""),
    code("""emb = ayuda.cargar_embeddings("data/alphaearth/black_river_2024.npz")
print("Forma:", emb.shape, "→ 64 números por píxel")

fig, ax = plt.subplots(1, 2, figsize=(12, 6))
ax[0].imshow(rgb_a); ax[0].set_title("Sentinel-2 (lo que ve una cámara)")
ax[1].imshow(ayuda.rgb_embeddings(emb)); ax[1].set_title("AlphaEarth 2024 (3 de 64 dimensiones como color)")
for a in ax: a.axis("off")
plt.show()"""),
    md("""Ahora le damos a AlphaEarth un ejemplo de **zona construida** (el centro de Black River) y le pedimos que encuentre todo lo que se parece.
Después **cruzamos** esa capa con el agua nueva del radar: **zonas construidas a menos de 250 m de agua nueva**. Así se mide la *exposición* en una evaluación rápida."""),
    code("""# @title Busca lugares parecidos a este punto { run: "auto" }
ref_lat, ref_lon = 18.033, -77.858   # centro del pueblo de Black River
UMBRAL_SIM = 0.90  # @param {type:"slider", min:0.6, max:0.98, step:0.01}

v = ayuda.vector_en(emb, bbox, ref_lat, ref_lon)
sim = ayuda.similitud(emb, v)
construido = sim > UMBRAL_SIM

agua_en_emb = ayuda.redimensionar(agua_nueva, construido.shape)   # misma cuadrícula que AlphaEarth
expuesto = construido & ayuda.cerca_de(agua_en_emb, bbox, metros=250)
km2_px = ayuda.km2_por_pixel(bbox, construido.shape)

fig, ax = plt.subplots(1, 2, figsize=(12, 6))
ax[0].imshow(sim, cmap="viridis", vmin=0.5, vmax=1); ax[0].set_title("Parecido al pueblo (1 = idéntico)")
ax[1].imshow(rgb_d); ax[1].set_title(f"Construido a <250 m de agua nueva ≈ {expuesto.sum() * km2_px:.2f} km²")
capa = ayuda.redimensionar(expuesto, rgb_d.shape[:2])
ax[1].imshow(np.ma.masked_where(~capa, capa), cmap="autumn", alpha=0.9)
for a in ax: a.axis("off")
plt.show()
print(f"Zona 'parecida a pueblo': {construido.sum() * km2_px:.2f} km² · de ella, junto a agua nueva: {expuesto.sum() * km2_px:.2f} km²")"""),
    md(KEY_MD + """

## Paso 5 · De los mapas a una alerta
Le pasamos los números a **Gemini** para que redacte un aviso claro: qué pasó, dónde y qué hacer."""),
    code("""cliente = ayuda.cliente_gemini()
modelo = ayuda.elegir_modelo(cliente, "flash")
datos = {
    "evento": "Huracán Melissa, inundación posterior",
    "zona": "Black River y alrededores, parroquia de St. Elizabeth, Jamaica",
    "fuente": "Satélites Sentinel-1 (radar, 29-oct-2025) y Sentinel-2, análisis automático",
    "agua_nueva_km2": round(float(km2), 1),
    "zona_construida_a_menos_de_250m_de_agua_nueva_km2": round(float(expuesto.sum() * km2_px), 2),
    "vegetacion": "pérdida fuerte de vegetación tras el huracán",
    "advertencia": "Estimación automática por satélite, sin validar en terreno",
}
ayuda.mostrar_alerta(ayuda.redactar_alerta(cliente, modelo, datos))"""),
    md("""## 🏁 Reto · Tu propio lugar
Cambia las coordenadas por tu barrio, el río cerca de tu casa o tu provincia. Usa una caja **pequeña** (3 km): leer AlphaEarth en vivo tarda **alrededor de un minuto por año**.
Compara 2017 con 2025: ¿qué cambió en ocho años? Busca, por ejemplo, la orilla del Ozama o la expansión de Santiago."""),
    code("""# @title Compara dos años en tu lugar
mi_lat, mi_lon = 18.4861, -69.9312  # @param {type:"number"}
anio_1, anio_2 = 2017, 2025          # @param {type:"raw"}
mi_bbox = ayuda.caja(mi_lat, mi_lon, km=3)

e1 = ayuda.embeddings_alphaearth(mi_bbox, anio_1, ancho=300)
e2 = ayuda.embeddings_alphaearth(mi_bbox, anio_2, ancho=300)
cambio = 1 - np.nansum(e1 * e2, 0) / (np.sqrt(np.nansum(e1**2, 0)) * np.sqrt(np.nansum(e2**2, 0)))

fig, ax = plt.subplots(1, 3, figsize=(15, 5))
ax[0].imshow(ayuda.rgb_embeddings(e1)); ax[0].set_title(str(anio_1))
ax[1].imshow(ayuda.rgb_embeddings(e2)); ax[1].set_title(str(anio_2))
im = ax[2].imshow(cambio, cmap="magma", vmin=0, vmax=0.6); ax[2].set_title("Cuánto cambió (claro = mucho)")
plt.colorbar(im, ax=ax[2], shrink=0.7)
for a in ax: a.axis("off")
plt.show()"""),
    md("""---
**Fuentes y licencias.** Sentinel-1 y Sentinel-2: Copernicus (ESA/UE), datos libres; Sentinel-2 L2A vía Earth Search (Element 84) y Sentinel-1 RTC vía Microsoft Planetary Computer.
AlphaEarth Foundations Satellite Embedding: Google DeepMind / Google Earth Engine, copia en Source Cooperative (CC BY 4.0).
Los análisis de este notebook son **didácticos**: un umbral de radar no sustituye una evaluación de daños oficial."""),
]

# ============================================================================ PISTA D
pista_d = [
    md(f"""# 🗺️ Pista D — Tu plataforma de vigilancia satelital con AlphaEarth
**Código que Salva Vidas · DevFest Santo Domingo 2026 · Taller · Nivel principiante**

[![Abrir en Colab](https://colab.research.google.com/assets/colab-badge.svg)]({COLAB}/pista_D_alphaearth.ipynb)

**Amazon Mining Watch** (Earth Genome) vigila con satélite la minería de oro en los nueve países amazónicos: 1,1 millones de hectáreas detectadas hasta 2026.
**Google Earth** acaba de estrenar *Classify*: le marcas unos ejemplos y te clasifica cultivos, bosque o barrios usando **AlphaEarth Foundations**.

Aquí construyes tu propia versión para **República Dominicana**, enfocada en **erosión y cambios del suelo**:

| Paso | Pregunta | Cómo |
|---|---|---|
| 1 | ¿Qué hay? | AlphaEarth (64 números por píxel de 10 m) y Sentinel-2 |
| 2 | ¿Dónde cambió entre 2017 y 2025? | Comparar las "huellas" de AlphaEarth de los dos años |
| 3 | ¿Ese cambio está en ladera? | Pendiente del modelo de elevación Copernicus |
| 4 | ¿Qué es cada cosa hoy? | Clasificar con unos pocos ejemplos, como Classify |
| 5 | ¿Cómo se lo explico a alguien? | Informe con Gemini |
| 6 | **Tu plataforma** | Una app web con Gradio y un enlace para compartir |

Todo con datos abiertos: **no necesitas proyecto de Google Cloud ni de Earth Engine.**
**Importante:** esto da *señales para revisar*, no diagnósticos. Un cambio en ladera puede ser erosión, una cosecha o una obra; hay que verificarlo en terreno."""),
    code(f"""# Instala lo necesario y trae el código del taller (~40 s)
!pip -q install rasterio pystac-client planetary-computer google-genai gradio scikit-learn
!wget -q -N https://raw.githubusercontent.com/{REPO}/main/taller/ayuda.py https://raw.githubusercontent.com/{REPO}/main/taller/plataforma.py
import ayuda, plataforma as pf, numpy as np, matplotlib.pyplot as plt
plt.rcParams.update({{"figure.dpi": 110, "font.size": 10}})
print("Listo ✅")"""),
    md("""## Paso 1 · Elige un lugar

Constanza tiene una **copia** de AlphaEarth de todos los años (carga al instante). Para los demás lugares, o tus propias coordenadas, se lee en vivo desde Source Cooperative: **alrededor de 1 minuto por año**."""),
    code("""# @title El lugar { run: "auto" }
lugar = "Constanza (laderas agrícolas)"  # @param ["Constanza (laderas agrícolas)", "Río Nizao, Los Cacaos (cauce)", "Cotuí (minería a cielo abierto)", "Juan Dolio (costa)", "Santiago (crecimiento urbano)"]
anio_a, anio_b = 2017, 2025

LAT, LON = pf.LUGARES_RD[lugar]
bbox = pf.zona(LAT, LON, km=4)
copia = "data/alphaearth/constanza_serie.npz" if lugar.startswith("Constanza") else None
serie = pf.serie_alphaearth(bbox, (anio_a, anio_b), copia=copia)
A, B = serie[anio_a], serie[anio_b]
print(lugar, "· caja de 4 km ·", B.shape[1:], "píxeles")"""),
    code("""rgb_s2, dia = pf.sentinel2_mediana(bbox, anio_b)   # foto real, escena más limpia de la estación seca
fig, ax = plt.subplots(1, 3, figsize=(15, 5))
ax[0].imshow(rgb_s2); ax[0].set_title(f"Sentinel-2 · {dia}")
ax[1].imshow(ayuda.rgb_embeddings(A)); ax[1].set_title(f"AlphaEarth {anio_a}")
ax[2].imshow(ayuda.rgb_embeddings(B)); ax[2].set_title(f"AlphaEarth {anio_b}")
for a in ax: a.axis("off")
plt.show()"""),
    md("""**🧠 Para pensar:** en AlphaEarth, colores parecidos significan terrenos parecidos. ¿Reconoces el valle, el pueblo y las laderas en la foto de Sentinel-2?

## Paso 2 y 3 · ¿Dónde cambió, y en qué pendiente?

Comparamos la "huella" de cada píxel en los dos años: **0 = igual, cuanto más alto, más cambió**.
Después calculamos la **pendiente** con el modelo de elevación **Copernicus GLO-30**, que es abierto y está en AWS.
Un cambio fuerte en un terreno empinado es una **señal**: ahí conviene mirar primero, porque es donde la erosión hace más daño.
El umbral de 0,15 deja pasar más o menos el 5 % de píxeles que más cambiaron. En Constanza casi todo el cambio está en el valle plano (rotación de cultivos); las señales aparecen en el borde de las laderas."""),
    code("""# @title Umbrales { run: "auto" }
UMBRAL_CAMBIO = 0.15     # @param {type:"slider", min:0.05, max:0.6, step:0.01}
PENDIENTE_MIN = 10       # @param {type:"slider", min:0, max:45, step:1}

cambio = pf.cambio(A, B)
pendiente = pf.pendiente_grados(bbox, cambio.shape)
senal = pf.señales_erosion(cambio, pendiente, UMBRAL_CAMBIO, PENDIENTE_MIN)

fig, ax = plt.subplots(1, 3, figsize=(15, 5))
im = ax[0].imshow(cambio, cmap="magma", vmin=0, vmax=0.5); ax[0].set_title(f"Cambio {anio_a}→{anio_b}"); plt.colorbar(im, ax=ax[0], shrink=0.7)
im = ax[1].imshow(pendiente, cmap="cividis", vmin=0, vmax=40); ax[1].set_title("Pendiente (°)"); plt.colorbar(im, ax=ax[1], shrink=0.7)
ax[2].imshow(pf.superponer(ayuda.rgb_embeddings(B), senal)); ax[2].set_title("Señales: cambio fuerte en ladera")
for a in ax: a.axis("off")
plt.show()
pf.resumen(bbox, cambio, pendiente, senal, umbral_cambio=UMBRAL_CAMBIO)"""),
    md("""## Paso 4 · Clasificar con ejemplos (como *Classify* de Google Earth)

Le damos a la máquina **unos pocos ejemplos** de cada clase (fila, columna en la imagen) y un **Random Forest** aprende a reconocerlas usando los 64 números de AlphaEarth.
Es exactamente lo que hace *Classify* en Google Earth, y la técnica con la que se mapean **tipos de cultivo** a escala de país.
Los ejemplos de abajo son para Constanza. En la plataforma del paso 6 los marcas tú con clics."""),
    code("""EJEMPLOS = pf.EJEMPLOS_CONSTANZA if lugar.startswith("Constanza") else []
if EJEMPLOS:
    etiquetas, clases = pf.clasificar(B, EJEMPLOS)
    fig, ax = plt.subplots(1, 2, figsize=(12, 6))
    ax[0].imshow(ayuda.rgb_embeddings(B))
    for f, c, k in EJEMPLOS:
        ax[0].scatter(c, f, s=40, color=pf.CLASES[k], edgecolor="black")
    ax[0].set_title("Tus ejemplos")
    ax[1].imshow(pf.colorear(etiquetas, clases)); ax[1].set_title("Clasificación de toda la zona")
    for a in ax: a.axis("off")
    plt.show()
    display(pf.resumen(bbox, cambio, pendiente, senal, etiquetas, clases))
else:
    print("Para otros lugares, marca tus ejemplos en la plataforma del paso 6.")"""),
    md(KEY_MD + """

## Paso 5 · El informe
Gemini convierte los números en un párrafo para alguien que no es técnico, sin inventar causas."""),
    code("""cliente = ayuda.cliente_gemini()
modelo = ayuda.elegir_modelo(cliente, "flash")
datos = pf.resumen(bbox, cambio, pendiente, senal, *( (etiquetas, clases) if EJEMPLOS else (None, None) ))
datos["lugar"] = lugar
r = cliente.models.generate_content(model=modelo, contents=(
    "Eres analista de riesgo ambiental en República Dominicana. Con estos números de un análisis satelital "
    "automático (AlphaEarth + pendiente Copernicus), escribe 5 líneas en español sencillo: qué cambió, dónde "
    "mirar primero y qué verificar en terreno. No inventes causas ni nombres; es una señal, no un diagnóstico.\\n"
    + str(datos)))
print(r.text)"""),
    md("""## Paso 6 · 🚀 Tu plataforma

La siguiente celda junta todo en una **app web** con Gradio. Al ejecutarla aparece un enlace `*.gradio.live` que puedes **compartir con quien quieras** durante 72 horas.
1. Elige un lugar y pulsa **Cargar**.
2. Elige una clase y **haz clic en la imagen de AlphaEarth** para marcar ejemplos (al menos 3 por clase).
3. Pulsa **Clasificar** y mueve los umbrales.
4. Pide el **informe** a Gemini."""),
    code("""pf.app(copias={"Constanza (laderas agrícolas)": "data/alphaearth/constanza_serie.npz"})"""),
    md("""## 🏁 Retos
1. Cambia el año A a **2020** y el B a **2025** en la plataforma. ¿Las señales se concentran en los mismos sitios?
2. En **Cotuí** o en el **río Nizao**, marca ejemplos de *Suelo desnudo* y *Agua*. ¿Qué parte de las señales es suelo expuesto hoy?
3. Busca tu provincia con *Mis coordenadas* y comparte el enlace de tu plataforma en el chat del GDG.

---
**Fuentes y licencias.** AlphaEarth Foundations Satellite Embedding: Google DeepMind / Earth Engine, copia en Source Cooperative (CC BY 4.0).
Copernicus DEM GLO-30 (© DLR/Airbus, licencia Copernicus, vía AWS Open Data). Sentinel-2 L2A: Copernicus (ESA/UE) vía Earth Search.
Inspiración: Amazon Mining Watch (Earth Genome y aliados) y Google Earth *Classify*. Los resultados son señales para verificar en terreno, no diagnósticos."""),
]

if __name__ == "__main__":
    notebook(pista_a, "pista_A_huracan.ipynb")
    notebook(pista_b, "pista_B_satelite.ipynb")
    notebook(pista_d, "pista_D_alphaearth.ipynb")
