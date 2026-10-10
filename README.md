# Código que salva vidas · Entendiendo Google Crisis Resilience

Taller de **DevFest Santo Domingo 2026** · nivel principiante.

En este taller usas productos de **Google Crisis Resilience** y datos abiertos de satélite para ir del pronóstico a la alerta.
Las pistas A y B siguen al **huracán Melissa** (Jamaica, 28 de octubre de 2025), desde el pronóstico hasta la alerta. La pista C construye una plataforma de vigilancia de erosión en República Dominicana con **AlphaEarth Foundations**. La pista D es un extra sin código, en AI Studio, para quien solo tenga el teléfono.

**Solo necesitas una cuenta de Google y un navegador.** No hace falta instalar nada, saber programar ni crear un proyecto de Google Cloud o de Earth Engine.

👉 **Portal del taller:** <https://alcastaro.github.io/codigo-que-salva-vidas/>

## Elige una pista

| Pista | Qué haces | Dónde | Abrir |
|---|---|---|---|
| **A · Huracán** | Ves los 50 escenarios de Weather Lab (Google DeepMind), calculas la probabilidad de que el huracán pase por un lugar y conviertes los números en una alerta con Gemini y Gemma | Colab, en laptop | [![Abrir en Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/alcastaro/codigo-que-salva-vidas/blob/main/taller/pista_A_huracan.ipynb) |
| **B · Satélite** | Buscas imágenes Sentinel-1 y Sentinel-2, detectas agua nueva con radar a través de las nubes y usas AlphaEarth para ver qué zonas construidas quedaron expuestas | Colab, en laptop | [![Abrir en Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/alcastaro/codigo-que-salva-vidas/blob/main/taller/pista_B_satelite.ipynb) |
| **C · AlphaEarth** | Detectas cambios del suelo 2017→2025 en laderas de RD, clasificas el terreno con unos pocos ejemplos y publicas tu propia plataforma web con Gradio | Colab, en laptop | [![Abrir en Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/alcastaro/codigo-que-salva-vidas/blob/main/taller/pista_C_alphaearth.ipynb) |
| **D · Alerta (extra)** | Sin código: das reglas a Gemini en AI Studio, lo obligas a responder en el formato estándar de alertas (CAP), lo comparas con Gemma y creas tu propia app con Build | AI Studio, sirve en el teléfono | [Guía paso a paso](taller/pista_D_ai_studio.md) |

Si no sabes cuál elegir: **A** si te interesa el clima, **B** si te interesan los satélites, **C** si quieres salir con una app propia. Si solo tienes el teléfono, prueba el extra **D**.

**¿Solo quieres ver los resultados?** Estas versiones ya están ejecutadas, con las figuras y los análisis de Gemini del ejemplo:
[Pista A](taller/resultados/pista_A_huracan_resultados.ipynb) · [Pista B](taller/resultados/pista_B_satelite_resultados.ipynb) · [Pista C](taller/resultados/pista_C_alphaearth_resultados.ipynb).

**¿Quieres analizar otro lugar?** En cada cuaderno, el formulario del lugar tiene la opción **«Mis coordenadas»**: elígela y escribe latitud y longitud (en Google Maps, clic derecho sobre el mapa).

## Paso 1 · Saca tu API key de Gemini (gratis, 2 minutos)

Las pistas A, B y C usan Gemini desde Colab, y para eso necesitas una **API key**: una clave personal que identifica tus llamadas al modelo. El extra D no la necesita.

1. Abre [aistudio.google.com/apikey](https://aistudio.google.com/apikey) con tu cuenta de Google.
2. Acepta los términos si es la primera vez.
3. Pulsa **Create API key** y copia la clave.

> **Trata la key como una contraseña.** Nunca la pegues dentro de una celda ni en un chat: si compartes el notebook o lo subes a GitHub, la key viaja con él y otra persona puede gastar tu cuota.

## Paso 2 · Abre tu pista en Colab y guarda una copia

1. Pulsa el botón **Abrir en Colab** de tu pista e inicia sesión con tu cuenta de Google.
2. En el menú, pulsa **File → Save a copy in Drive** (*Archivo → Guardar una copia en Drive*). Trabaja en esa copia: es tuya y guarda tus cambios.

## Paso 3 · Guarda la key en los Secretos de Colab

1. En la barra de la izquierda de Colab, abre el icono de la **llave 🔑 (Secretos)**.
2. Pulsa **Add new secret** (*Agregar secreto nuevo*).
3. En *Name* escribe exactamente `GOOGLE_API_KEY`. En *Value* pega tu key.
4. Activa el interruptor **Notebook access** (*Acceso al notebook*).

Atajo: en ese mismo panel, **Gemini API keys → Import key from Google AI Studio** crea y guarda la key por ti.

Cuando el notebook use la key por primera vez, Colab puede preguntar si le das permiso: pulsa **Grant access** (*Otorgar acceso*).

## Paso 4 · Ejecuta las celdas en orden

- Haz clic en una celda y pulsa ▶️ a su izquierda, o `Shift + Enter`. Ve de arriba abajo, sin saltarte ninguna.
- La primera vez, Colab avisa *"This notebook was not authored by Google"*. Pulsa **Run anyway** (*Ejecutar de todos modos*). El código es el de este repositorio y puedes leerlo entero.
- Las celdas con formulario a la derecha (desplegables, deslizadores, casillas) se cambian sin tocar el código.
- Algunas celdas tienen la casilla `LIVE`. Si la dejas en `False`, se usa una copia de los datos guardada en este repositorio y la celda tarda segundos. Si la activas, se leen los satélites en directo y puede tardar minutos.

**Cada cuaderno es autocontenido.** Todo el código está dentro: cada paso define sus funciones, con comentarios que explican qué hace cada parte, y luego las usa. No se importa ningún archivo externo.

**No tienes que descargar datos a mano.** La función `download()` de la primera celda baja de la carpeta [`data/`](data/) de este repositorio cada archivo que hace falta, la primera vez que hace falta, y lo guarda en la carpeta `workshop_data/` de tu sesión de Colab.

**Cada cuaderno explica cómo leer cada resultado** (después de cada figura, en un bloque 📖) y **cómo adaptarlo**: otro huracán y otra ciudad en la pista A, otro lugar u otro desastre en la B, otra región, otros años u otra pregunta en la C.

## Si algo falla

| Lo que ves | Qué hacer |
|---|---|
| `NameError: name '...' is not defined` | Te saltaste una celda: cada paso usa funciones definidas antes. Usa **Runtime → Run before** (*Entorno de ejecución → Ejecutar anteriores*). |
| `ModuleNotFoundError` | Ejecuta otra vez la primera celda (la que instala librerías). |
| `HTTP Error 404` al descargar | La dirección no existe: revisa la fecha o el identificador que escribiste. |
| `No encuentro tu key` o `Falta GOOGLE_API_KEY` | Revisa el paso 3: el nombre debe ser exactamente `GOOGLE_API_KEY` y *Notebook access* debe estar activo. |
| `429` o `RESOURCE_EXHAUSTED` | Llegaste al límite gratuito por minuto. Espera un minuto y vuelve a ejecutar la celda. |
| `503` o `UNAVAILABLE` | El modelo está saturado. El código reintenta solo; si aun así falla, prueba de nuevo en un minuto. |
| Una celda tarda mucho | Pon `LIVE` en `False` para usar la copia guardada. |
| Todo se rompió | **Runtime → Restart session** y ejecuta desde la primera celda. |

## Qué hay en este repositorio

| Carpeta o archivo | Contenido |
|---|---|
| `taller/pista_A_huracan.ipynb`, `pista_B_satelite.ipynb`, `pista_C_alphaearth.ipynb` | Los notebooks de Colab, cada uno con todo su código |
| `taller/resultados/` | Las mismas pistas ya ejecutadas, para leer los resultados sin correr nada |
| `taller/pista_D_ai_studio.md` | La guía del extra D, para seguir en AI Studio |
| `data/melissa/` | Pronósticos de Weather Lab (22, 25 y 27 de octubre de 2025) y trayectoria real del NHC |
| `data/sentinel/black_river.npz` | Copia de las imágenes Sentinel-1 y Sentinel-2 de Black River, antes y después |
| `data/alphaearth/` | Copias de AlphaEarth: Black River 2024 y Constanza 2017–2025 |
| `data/aef_index_light.parquet` | Índice que dice qué archivo de AlphaEarth cubre cada lugar y año |
| `data/caribbean_countries.geojson` | Contornos de países para los mapas |
| `index.html` | El portal del taller |
| `requirements.txt` | Librerías, por si quieres ejecutar los notebooks en tu computadora en vez de en Colab |

## Datos, fuentes y licencias

| Dato | Fuente | Licencia / condiciones |
|---|---|---|
| Pronósticos de ciclón (50 escenarios) | Google DeepMind **Weather Lab**, modelo experimental | Históricos: **CC BY 4.0**. Pronóstico de investigación, no producto oficial |
| Trayectoria real de Melissa | NOAA / National Hurricane Center, best track AL132025 | Dominio público (gobierno de EE. UU.) |
| Sentinel-2 L2A | Copernicus (ESA/UE) vía Earth Search (Element 84) | Datos Copernicus libres y abiertos |
| Sentinel-1 RTC | Copernicus (ESA/UE) vía Microsoft Planetary Computer | Datos Copernicus libres y abiertos |
| Satellite Embedding (AlphaEarth Foundations) | Google DeepMind / Earth Engine, copia en Source Cooperative | **CC BY 4.0** |
| Elevación (pendiente) | Copernicus DEM GLO-30 vía AWS Open Data | Licencia Copernicus DEM (© DLR/Airbus), uso libre con atribución |
| Contornos de países | Natural Earth | Dominio público |

**Aviso:** material didáctico. Los resultados son señales para revisar, no diagnósticos ni alertas oficiales. Para alertas reales, consulta a tu servicio meteorológico nacional.
