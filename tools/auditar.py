"""Auditoría: ejecuta cada notebook como lo haría Colab, en una carpeta vacía y bajando todo de un
servidor que imita a raw.githubusercontent.com (o del GitHub real con --github).

    .venv/bin/python tools/auditar.py            # servidor local con el repo
    .venv/bin/python tools/auditar.py --github   # versión publicada

Salida en auditoria/: cada notebook ejecutado (.ipynb y .html) e INFORME.md con el estado de cada celda.
Diferencias con Colab: no se ejecuta `pip` (el entorno local ya tiene las librerías), `wget` se cambia por
`curl` (macOS no trae wget) y la celda que lanza la app Gradio se sustituye por un aviso, porque se queda
corriendo; la app se prueba aparte con el navegador.
"""
import os
import sys
import threading
import time
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import nbformat
from nbclient import NotebookClient
from nbconvert import HTMLExporter

RAIZ = Path(__file__).resolve().parents[1]
OUT = RAIZ / "auditoria"
GITHUB = "https://raw.githubusercontent.com/alcastaro/codigo-que-salva-vidas/main"
PISTAS = ["pista_A_huracan", "pista_B_satelite", "pista_D_alphaearth"]


def servidor() -> str:
    h = partial(SimpleHTTPRequestHandler, directory=str(RAIZ))
    h.log_message = lambda *a: None
    srv = ThreadingHTTPServer(("127.0.0.1", 8765), h)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return "http://127.0.0.1:8765"


def adaptar(nb, raw: str):
    for c in nb.cells:
        if c.cell_type != "code":
            continue
        lineas = []
        for l in c.source.splitlines():
            if l.lstrip().startswith("!pip"):
                lineas.append("# (auditoría local: pip omitido) " + l.strip())
            elif l.lstrip().startswith("!wget"):
                urls = [u.replace(GITHUB, raw) for u in l.split() if u.startswith("http")]
                lineas.extend(f"!curl -s -f -O {u}" for u in urls)
            else:
                lineas.append(l)
        c.source = "\n".join(lineas)
        if "pf.app(" in c.source:
            c.source = 'print("(auditoría: la app Gradio se prueba aparte con el navegador)")'


def main():
    raw = GITHUB if "--github" in sys.argv else servidor()
    os.environ["TALLER_RAW"] = raw
    env = RAIZ / ".env"  # ignorado por git: GOOGLE_API_KEY=... para probar también las celdas de Gemini
    if env.exists():
        for linea in env.read_text().splitlines():
            if linea.startswith("GOOGLE_API_KEY="):
                os.environ["GOOGLE_API_KEY"] = linea.split("=", 1)[1].strip().strip('"')
    informe = [f"# Auditoría de los notebooks\n\nFuente de datos: `{raw}` · {time.strftime('%Y-%m-%d %H:%M')}\n"]
    for nombre in PISTAS:
        carpeta = OUT / nombre
        carpeta.mkdir(parents=True, exist_ok=True)
        for f in carpeta.glob("*.py"):
            f.unlink()  # carpeta limpia: ayuda.py y plataforma.py se bajan como en Colab
        nb = nbformat.read(RAIZ / "taller" / f"{nombre}.ipynb", as_version=4)
        adaptar(nb, raw)
        t0 = time.time()
        NotebookClient(nb, timeout=1200, allow_errors=True, kernel_name="python3",
                       resources={"metadata": {"path": str(carpeta)}}).execute()
        nbformat.write(nb, carpeta / f"{nombre}_ejecutado.ipynb")
        html, _ = HTMLExporter().from_notebook_node(nb)
        (carpeta / f"{nombre}_ejecutado.html").write_text(html)
        informe.append(f"\n## {nombre} · {time.time() - t0:.0f} s\n\n| Celda | Estado | Detalle |\n|---|---|---|")
        for i, c in enumerate(nb.cells):
            if c.cell_type != "code":
                continue
            errs = [o for o in c.get("outputs", []) if o.get("output_type") == "error"]
            primera = c.source.strip().splitlines()[0][:60] if c.source.strip() else ""
            if errs:
                det = f"{errs[0]['ename']}: {errs[0]['evalue'][:120]}".replace("|", "/").replace("\n", " ")
                informe.append(f"| {i} | ❌ | `{primera}` → {det} |")
            else:
                informe.append(f"| {i} | ✅ | `{primera}` |")
        print(nombre, "listo")
    (OUT / "INFORME.md").write_text("\n".join(informe) + "\n")
    print((OUT / "INFORME.md").read_text())


if __name__ == "__main__":
    main()
