# Código que salva vidas · Entendiendo Google Crisis Resilience

Taller de **DevFest Santo Domingo 2026** (track Workshops, sala Laboratorio, nivel principiante, 40 min).
Alberto Castillo Aroca · GDG Santo Domingo.

Las pistas A, B y C siguen al **huracán Melissa** (Jamaica, 28 de octubre de 2025), desde el pronóstico hasta la alerta,
con productos de Google Crisis Resilience y datos abiertos. La D construye una plataforma de vigilancia de erosión en RD con AlphaEarth, inspirada en Amazon Mining Watch. **No hace falta proyecto de Google Cloud ni Earth Engine.**

| Pista | Qué se hace | Herramienta | Dónde |
|---|---|---|---|
| **A · Huracán** | 50 escenarios de Weather Lab, probabilidad de paso, alerta con Gemini y Gemma (Flood Hub solo se muestra) | Colab | [`taller/pista_A_huracan.ipynb`](taller/pista_A_huracan.ipynb) |
| **B · Satélite** | Sentinel-1/2 con STAC, agua nueva por radar, AlphaEarth (búsqueda por similitud), alerta | Colab | [`taller/pista_B_satelite.ipynb`](taller/pista_B_satelite.ipynb) |
| **C · Alerta** | Instrucciones de sistema, salida estructurada CAP, Gemma, app con Build | AI Studio (sirve en el móvil) | [`taller/pista_C_ai_studio.md`](taller/pista_C_ai_studio.md) |
| **D · AlphaEarth** | Erosión en RD: cambio 2017→2025 × pendiente, clasificación con ejemplos (como Google Earth *Classify*), plataforma Gradio | Colab | [`taller/pista_D_alphaearth.ipynb`](taller/pista_D_alphaearth.ipynb) |

Portal para el QR: [`index.html`](index.html) (GitHub Pages).

## Cómo empezar

1. Abre el [portal](https://alcastaro.github.io/codigo-que-salva-vidas/) y elige una pista.
2. Saca tu API key gratuita de Gemini en [aistudio.google.com/apikey](https://aistudio.google.com/apikey).
3. En Colab, guárdala en la llave 🔑 (Secretos) con el nombre `GOOGLE_API_KEY` y activa *Notebook access*. Nunca la pegues en una celda.
4. Ejecuta las celdas en orden. Las celdas pesadas traen una copia de los datos (`EN_VIVO = False`) para no depender de la red.

## Qué hay en este repositorio

| Carpeta | Contenido |
|---|---|
| `taller/` | Los notebooks de las pistas A, B y D, la guía de la pista C y el código de apoyo (`ayuda.py`, `plataforma.py`) |
| `data/` | Copias de los datos abiertos que usan los notebooks |
| `index.html` | El portal del taller (GitHub Pages) |

## Datos, fuentes y licencias

| Dato | Fuente | Licencia / condiciones |
|---|---|---|
| Pronósticos de ciclón (50 escenarios) | Google DeepMind **Weather Lab**, modelo experimental | Históricos: **CC BY 4.0**. Pronóstico de investigación, no producto oficial |
| Trayectoria real de Melissa | NOAA / National Hurricane Center, best track AL132025 | Dominio público (gobierno de EE. UU.) |
| Estado de ríos | Google **Flood Forecasting API** (Flood Hub) | Solo uso no comercial; acceso con key aprobada |
| Sentinel-2 L2A | Copernicus (ESA/UE) vía Earth Search (Element 84) | Datos Copernicus libres y abiertos |
| Sentinel-1 RTC | Copernicus (ESA/UE) vía Microsoft Planetary Computer | Datos Copernicus libres y abiertos |
| Satellite Embedding (AlphaEarth Foundations) | Google DeepMind / Earth Engine, copia en Source Cooperative | **CC BY 4.0** |
| Elevación (pendiente) | Copernicus DEM GLO-30 vía AWS Open Data | Licencia Copernicus DEM (© DLR/Airbus), uso libre con atribución |
| Contornos de países | Natural Earth | Dominio público |
| Capturas y GIF de plataformas | crisisresilience.google, Flood Hub, WeatherNext, Earth Engine, Google Earth, Amazon Mining Watch, Climate Engine | Capturas de pantalla para comentario educativo, con la fuente en cada diapositiva |
| Diseño del deck | Sistema de diseño DevFest Santo Domingo / Google Developer Groups | Uso del capítulo |

Cifras citadas en el deck (con la fuente en las notas de cada diapositiva): crisisresilience.google;
Allen et al., *Science* (2025); Nearing et al., *Nature* (2024); blogs de Google DeepMind sobre WeatherNext 2,
Melissa y AlphaEarth; anuncio de ganadores del Gemma 4 Good Challenge (blog de Google, 24-ago-2026); Google Earth AI (Google Research, 23-oct-2025); documentación de Google Earth *Classify*; Earth Genome, actualización de Amazon Mining Watch (agosto 2026); Climate Engine (DRI y Universidad de Idaho).

**Aviso:** material didáctico. Para alertas reales, consulta a tu servicio meteorológico nacional.
