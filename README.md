# Código que salva vidas · Entendiendo Google Crisis Resilience

Taller de **DevFest Santo Domingo 2026** (track Workshops, sala Laboratorio, nivel principiante, 40 min).
Alberto Castillo Aroca · GDG Santo Domingo.

Las tres pistas siguen al **huracán Melissa** (Jamaica, 28 de octubre de 2025), desde el pronóstico hasta la alerta,
con productos de Google Crisis Resilience y datos abiertos. **No hace falta proyecto de Google Cloud ni Earth Engine.**

| Pista | Qué se hace | Herramienta | Dónde |
|---|---|---|---|
| **A · Huracán** | 50 escenarios de Weather Lab, probabilidad de paso, Flood Hub, alerta con Gemini y Gemma | Colab | [`taller/pista_A_huracan.ipynb`](taller/pista_A_huracan.ipynb) |
| **B · Satélite** | Sentinel-1/2 con STAC, agua nueva por radar, AlphaEarth (búsqueda por similitud), alerta | Colab | [`taller/pista_B_satelite.ipynb`](taller/pista_B_satelite.ipynb) |
| **C · Alerta** | Instrucciones de sistema, salida estructurada CAP, Gemma, app con Build | AI Studio (sirve en el móvil) | [`taller/pista_C_ai_studio.md`](taller/pista_C_ai_studio.md) |

Portal para el QR: [`index.html`](index.html) (GitHub Pages). Deck: [`deck/codigo-que-salva-vidas.pptx`](deck/codigo-que-salva-vidas.pptx).

## Guion de los 40 minutos

| Min | Bloque | Diapositivas |
|---|---|---|
| 0–1 | Portada; pedir que escaneen el QR **ya** (Colab tarda ~30 s en instalar) | 1 |
| 1–4 | El problema y el mapa de Crisis Resilience | 2–5 |
| 4–6 | Pilar 1 · Telemetría distribuida (sismos con Android) | 6–8 |
| 6–11 | Pilar 2 · Modelado predictivo (Flood Hub, WeatherNext, Sentinel, AlphaEarth) | 9–15 |
| 11–13 | Pilar 3 · Despliegue a escala + casos Gemma 4 Good | 16–18 |
| 13–14 | Elegir pista | 19 |
| 14–37 | **Taller.** Facilitador: 3 min de demo guiada de cada pista en pantalla, luego circula | — |
| 37–40 | Cierre | 20 |

**Plan B si cae la red:** todas las celdas pesadas tienen copia en `data/` y el interruptor `EN_VIVO` sale en `False`
por defecto. El deck no necesita internet.

## Antes del taller (facilitador)

1. **Flood Hub.** La API exige key aprobada. Guarda la tuya en `.env` (ignorado por git) como
   `FLOODHUB_API_KEY=...` y corre:
   ```bash
   .venv/bin/python tools/floodhub_extract.py --probe   # comprueba que la key responde
   .venv/bin/python tools/floodhub_extract.py           # genera data/floodhub/*.json
   ```
   Revisa los JSON antes de publicarlos: no deben contener la key (va en una cabecera, no en la URL).
2. **Fuentes del deck:** Google Sans y Roboto Mono (OFL). PowerPoint necesita los pesos estáticos
   Roboto Mono Thin y Light instalados; están en `deck/fonts/`.
3. **Prueba en Colab real** con una cuenta que no sea la tuya, desde la red del evento si es posible.

## Regenerar todo

```bash
uv venv .venv && uv pip install --python .venv/bin/python -r requirements.txt
.venv/bin/python tools/construir_notebooks.py           # notebooks desde una sola fuente
.venv/bin/python tools/probar_notebook.py taller/pista_A_huracan.ipynb
.venv/bin/python tools/probar_notebook.py taller/pista_B_satelite.ipynb
.venv/bin/python tools/preparar_alphaearth.py           # copia de embeddings (lento: ~6 min)
.venv/bin/python tools/preparar_copias_sentinel.py      # copia de Sentinel-1/2
.venv/bin/python tools/figuras_deck.py && .venv/bin/python tools/construir_deck.py
```

## Datos, fuentes y licencias

| Dato | Fuente | Licencia / condiciones |
|---|---|---|
| Pronósticos de ciclón (50 escenarios) | Google DeepMind **Weather Lab**, modelo experimental | Históricos: **CC BY 4.0**. Pronóstico de investigación, no producto oficial |
| Trayectoria real de Melissa | NOAA / National Hurricane Center, best track AL132025 | Dominio público (gobierno de EE. UU.) |
| Estado de ríos | Google **Flood Forecasting API** (Flood Hub) | Solo uso no comercial; acceso con key aprobada |
| Sentinel-2 L2A | Copernicus (ESA/UE) vía Earth Search (Element 84) | Datos Copernicus libres y abiertos |
| Sentinel-1 RTC | Copernicus (ESA/UE) vía Microsoft Planetary Computer | Datos Copernicus libres y abiertos |
| Satellite Embedding (AlphaEarth Foundations) | Google DeepMind / Earth Engine, copia en Source Cooperative | **CC BY 4.0** |
| Contornos de países | Natural Earth | Dominio público |
| Diseño del deck | Sistema de diseño DevFest Santo Domingo / Google Developer Groups | Uso del capítulo |

Cifras citadas en el deck (con la fuente en las notas de cada diapositiva): crisisresilience.google;
Allen et al., *Science* (2025); Nearing et al., *Nature* (2024); blogs de Google DeepMind sobre WeatherNext 2,
Melissa y AlphaEarth; anuncio de ganadores del Gemma 4 Good Challenge (blog de Google, 24-ago-2026).

**Aviso:** material didáctico. Para alertas reales, consulta a tu servicio meteorológico nacional.
