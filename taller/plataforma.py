"""Mini plataforma de vigilancia satelital con AlphaEarth (Pista D del taller).

Tres preguntas sobre un lugar de República Dominicana:
  1. ¿Qué hay?            → AlphaEarth + Sentinel-2
  2. ¿Qué es cada cosa?   → clasificación con ejemplos (como «Classify» de Google Earth)
  3. ¿Dónde cambió, y en qué pendiente? → cambio 2017→2025 × pendiente = señales de erosión

Inspirado en plataformas como Amazon Mining Watch (Earth Genome): detectar cambios del suelo
con satélite y priorizar dónde mirar. Escrito desde cero para este taller.
"""

import math

import numpy as np

import ayuda

# Lugares de ejemplo en RD. Son puntos para explorar, no diagnósticos.
LUGARES_RD = {
    "Constanza (laderas agrícolas)": (18.910, -70.745),
    "Río Nizao, Los Cacaos (cauce)": (18.520, -70.320),
    "Cotuí (minería a cielo abierto)": (18.940, -70.170),
    "Juan Dolio (costa)": (18.425, -69.430),
    "Santiago (crecimiento urbano)": (19.451, -70.697),
}
# Ejemplos para Constanza en la cuadrícula de 300×300 (fila, columna), elegidos sobre Sentinel-2 del 12-ene-2025.
EJEMPLOS_CONSTANZA = (
    [(20, 40, "Bosque"), (40, 250, "Bosque"), (275, 30, "Bosque"), (60, 15, "Bosque"), (15, 280, "Bosque")]
    + [(150, 150, "Construido"), (185, 140, "Construido"), (120, 170, "Construido"), (205, 115, "Construido")]
    + [(195, 215, "Cultivo / pasto"), (105, 215, "Cultivo / pasto"), (240, 282, "Cultivo / pasto"), (135, 258, "Cultivo / pasto")]
    + [(218, 268, "Suelo desnudo"), (268, 168, "Suelo desnudo"), (130, 95, "Suelo desnudo"), (262, 232, "Suelo desnudo")]
)
CLASES = {"Bosque": "#34a853", "Cultivo / pasto": "#f9ab00", "Suelo desnudo": "#ea4335",
          "Construido": "#9e9e9e", "Agua": "#4285f4"}


# ------------------------------------------------------------------ datos
def zona(lat: float, lon: float, km: float = 4.0) -> tuple:
    return ayuda.caja(lat, lon, km)


def serie_alphaearth(bbox: tuple, anios=(2017, 2025), ancho: int = 300, copia: str | None = None) -> dict:
    """Embeddings de AlphaEarth por año. Con `copia`, los lee de un .npz del repo (instantáneo)."""
    if copia:
        s = np.load(ayuda.dato(copia))
        deq = lambda q: np.where(q == -128, np.nan, np.sign(q) * (q.astype("float32") / 127.5) ** 2)  # noqa: E731
        return {y: deq(s[f"a{y}"]) for y in anios if f"a{y}" in s.files}
    return {y: ayuda.embeddings_alphaearth(bbox, y, ancho) for y in anios}


def pendiente_grados(bbox: tuple, forma: tuple) -> np.ndarray:
    """Pendiente del terreno (grados) desde el modelo de elevación Copernicus GLO-30 (abierto, en AWS)."""
    lat, lon = (bbox[1] + bbox[3]) / 2, (bbox[0] + bbox[2]) / 2
    ns, ew = ("N" if lat >= 0 else "S"), ("E" if lon >= 0 else "W")
    nombre = f"Copernicus_DSM_COG_10_{ns}{abs(math.floor(lat)):02d}_00_{ew}{abs(math.floor(lon)):03d}_00_DEM"
    url = f"/vsicurl/https://copernicus-dem-30m.s3.amazonaws.com/{nombre}/{nombre}.tif"
    z = ayuda.leer_en_caja(url, bbox, forma[1])[0].astype("float32")
    z = ayuda.redimensionar(z, forma)
    lado_m = math.sqrt(ayuda.km2_por_pixel(bbox, forma)) * 1000
    gy, gx = np.gradient(z, lado_m)
    return np.degrees(np.arctan(np.hypot(gx, gy)))


def sentinel2_mediana(bbox: tuple, anio: int, ancho: int = 400) -> tuple[np.ndarray, str]:
    """Color real de Sentinel-2 de la escena más limpia de la estación seca (ene–abr) de ese año."""
    s2 = ayuda.buscar_escenas("sentinel-2-l2a", bbox, f"{anio}-01-01/{anio}-04-30", max_nubes=20)
    if s2.empty:
        s2 = ayuda.buscar_escenas("sentinel-2-l2a", bbox, f"{anio}-01-01/{anio}-12-31", max_nubes=20)
    dia = s2.sort_values("nubes_%").fecha.iloc[0][:10]
    items = list(s2[s2.fecha.str.startswith(dia)].item)
    return ayuda.sentinel2(items, bbox, ancho)["rgb"], dia


# ------------------------------------------------------------------ análisis
def cambio(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """1 − similitud coseno entre dos años: 0 = igual, cuanto más alto, más cambió."""
    num = np.nansum(a * b, 0)
    den = np.sqrt(np.nansum(a ** 2, 0)) * np.sqrt(np.nansum(b ** 2, 0))
    return 1 - num / np.where(den == 0, np.nan, den)


def clasificar(emb: np.ndarray, ejemplos: list[tuple[int, int, str]]):
    """Random Forest sobre los 64 números de AlphaEarth, entrenado con los clics del usuario.

    ejemplos: [(fila, columna, clase), ...]. Se toma una vecindad de 3×3 píxeles por clic.
    """
    from sklearn.ensemble import RandomForestClassifier
    c, h, w = emb.shape
    X, y = [], []
    for f, col, clase in ejemplos:
        for df in (-1, 0, 1):
            for dc in (-1, 0, 1):
                ff, cc = min(max(f + df, 0), h - 1), min(max(col + dc, 0), w - 1)
                v = emb[:, ff, cc]
                if not np.isnan(v).any():
                    X.append(v); y.append(clase)
    if len(set(y)) < 2:
        raise ValueError("Marca ejemplos de al menos dos clases.")
    rf = RandomForestClassifier(n_estimators=120, random_state=0, n_jobs=-1).fit(X, y)
    plano = np.nan_to_num(emb.reshape(c, -1).T)
    etiquetas = rf.predict(plano).reshape(h, w)
    return etiquetas, list(rf.classes_)


def señales_erosion(cambio_: np.ndarray, pendiente: np.ndarray, umbral_cambio: float = 0.15,
                    umbral_pendiente: float = 10.0) -> np.ndarray:
    """Cambio fuerte en terreno empinado: dónde conviene mirar primero (no es un diagnóstico)."""
    return (cambio_ > umbral_cambio) & (pendiente > umbral_pendiente)


def resumen(bbox, cambio_, pendiente, senal, etiquetas=None, clases=None, umbral_cambio=0.15) -> dict:
    px = ayuda.km2_por_pixel(bbox, cambio_.shape)
    r = {
        "area_km2": round(cambio_.size * px, 1),
        "cambio_medio": round(float(np.nanmean(cambio_)), 3),
        "km2_con_cambio_fuerte": round(float(np.nansum(cambio_ > umbral_cambio) * px), 2),
        "km2_en_pendiente_mayor_10": round(float(np.nansum(pendiente > 10) * px), 2),
        "km2_senal_erosion": round(float(senal.sum() * px), 2),
    }
    if etiquetas is not None:
        r["que_hay_hoy_en_las_senales_km2"] = {
            str(k): round(float(((etiquetas == k) & senal).sum() * px), 3) for k in clases}
    return r


# ------------------------------------------------------------------ figuras
def colorear(etiquetas, clases) -> np.ndarray:
    from matplotlib.colors import to_rgb
    out = np.zeros(etiquetas.shape + (3,))
    for k in clases:
        out[etiquetas == k] = to_rgb(CLASES.get(k, "#000000"))
    return out


def superponer(fondo: np.ndarray, mascara: np.ndarray, color=(0.92, 0.26, 0.21)) -> np.ndarray:
    """Fondo apagado en grises y la máscara en rojo, engrosada 2 píxeles solo para que se vea."""
    from scipy.ndimage import binary_dilation
    f = ayuda.redimensionar(fondo, mascara.shape) if fondo.shape[:2] != mascara.shape else fondo
    gris = f.mean(axis=2, keepdims=True)
    out = np.repeat(0.35 + 0.45 * gris, 3, axis=2)
    out[binary_dilation(mascara, iterations=2)] = color
    return out


# ------------------------------------------------------------------ la app
def app(copias: dict | None = None, compartir: bool = True):
    """Lanza la plataforma con Gradio. `copias`: {nombre_lugar: ruta .npz} para no esperar la descarga."""
    import gradio as gr
    copias = copias or {}
    estado = {}

    def cargar(lugar, lat, lon, anio_a, anio_b):
        if lugar in LUGARES_RD:
            lat, lon = LUGARES_RD[lugar]
        bbox = zona(lat, lon)
        anios = (int(anio_a), int(anio_b))
        serie = serie_alphaearth(bbox, anios, copia=copias.get(lugar))
        a, b = serie[anios[0]], serie[anios[1]]
        cam = cambio(a, b)
        pend = pendiente_grados(bbox, cam.shape)
        estado.update(bbox=bbox, a=a, b=b, cambio=cam, pendiente=pend, ejemplos=[], lugar=lugar)
        rgb_b = ayuda.rgb_embeddings(b)
        estado["rgb_b"] = rgb_b
        senal = señales_erosion(cam, pend)
        return (rgb_b, np.clip(cam / 0.5, 0, 1), np.clip(pend / 40, 0, 1), superponer(rgb_b, senal),
                resumen(bbox, cam, pend, senal), "Haz clic en la imagen de AlphaEarth para marcar ejemplos.")

    def marcar(clase, evt: gr.SelectData):
        col, fila = evt.index
        estado.setdefault("ejemplos", []).append((int(fila), int(col), clase))
        n = {k: sum(1 for e in estado["ejemplos"] if e[2] == k) for k in CLASES}
        return ", ".join(f"{k}: {v}" for k, v in n.items() if v)

    def clasificar_ui(umbral_c, umbral_p):
        et, clases = clasificar(estado["b"], estado["ejemplos"])
        senal = señales_erosion(estado["cambio"], estado["pendiente"], umbral_c, umbral_p)
        estado.update(etiquetas=et, clases=clases, senal=senal)
        return (colorear(et, clases), superponer(estado["rgb_b"], senal),
                resumen(estado["bbox"], estado["cambio"], estado["pendiente"], senal, et, clases, umbral_c))

    def informe():
        cli = ayuda.cliente_gemini()
        modelo = ayuda.elegir_modelo(cli, "flash")
        datos = resumen(estado["bbox"], estado["cambio"], estado["pendiente"], estado.get("senal", señales_erosion(estado["cambio"], estado["pendiente"])),
                        estado.get("etiquetas"), estado.get("clases"))
        datos["lugar"] = estado.get("lugar")
        r = cli.models.generate_content(model=modelo, contents=(
            "Eres analista de riesgo ambiental en República Dominicana. Con estos números de un análisis "
            "satelital automático (AlphaEarth + pendiente Copernicus), escribe 5 líneas en español sencillo: "
            "qué cambió, dónde mirar primero y qué verificar en terreno. No inventes causas ni nombres; "
            "deja claro que es una señal para revisar, no un diagnóstico.\n" + str(datos)))
        return r.text

    with gr.Blocks(title="Vigilancia satelital · DevFest SDQ") as demo:
        gr.Markdown("## 🛰️ Mi plataforma de vigilancia satelital\nAlphaEarth Foundations + pendiente del terreno · "
                    "señales para revisar, no diagnósticos.")
        with gr.Row():
            lugar = gr.Dropdown(list(LUGARES_RD) + ["Mis coordenadas"], value=list(LUGARES_RD)[0], label="Lugar")
            lat = gr.Number(18.4861, label="Latitud (si eliges «Mis coordenadas»)")
            lon = gr.Number(-69.9312, label="Longitud")
            anio_a = gr.Dropdown([str(y) for y in range(2017, 2026)], value="2017", label="Año A")
            anio_b = gr.Dropdown([str(y) for y in range(2017, 2026)], value="2025", label="Año B")
        boton = gr.Button("1 · Cargar el lugar", variant="primary")
        with gr.Row():
            img_emb = gr.Image(label="AlphaEarth (año B) · haz clic para marcar ejemplos", interactive=False)
            img_cambio = gr.Image(label="Cambio A→B (claro = mucho)")
            img_pend = gr.Image(label="Pendiente (claro = empinado)")
            img_senal = gr.Image(label="Señales: cambio fuerte en ladera")
        with gr.Row():
            clase = gr.Radio(list(CLASES), value="Bosque", label="Clase del próximo clic")
            conteo = gr.Textbox(label="Ejemplos marcados (mínimo 3 por clase)")
        with gr.Row():
            u_c = gr.Slider(0.05, 0.6, 0.15, step=0.01, label="Umbral de cambio")
            u_p = gr.Slider(0, 45, 10, step=1, label="Pendiente mínima (°)")
            boton2 = gr.Button("2 · Clasificar y recalcular", variant="primary")
        with gr.Row():
            img_clases = gr.Image(label="Qué hay hoy (clasificación)")
            img_senal2 = gr.Image(label="Señales con tus umbrales")
            tabla = gr.JSON(label="Resumen")
        boton3 = gr.Button("3 · Informe con Gemini")
        texto = gr.Markdown()
        boton.click(cargar, [lugar, lat, lon, anio_a, anio_b], [img_emb, img_cambio, img_pend, img_senal, tabla, conteo])
        img_emb.select(marcar, [clase], conteo)
        boton2.click(clasificar_ui, [u_c, u_p], [img_clases, img_senal2, tabla])
        boton3.click(informe, None, texto)
    demo.launch(share=compartir, debug=False)
    return demo
