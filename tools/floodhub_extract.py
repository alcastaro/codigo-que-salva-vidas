"""Extrae una copia de Flood Hub (Google Flood Forecasting API) para el taller.

La API exige una key aprobada, así que el público no puede consultarla. Este script
la corre una sola vez con la key de quien da el taller y guarda las respuestas en
data/floodhub/ para que el notebook las lea desde GitHub.

La key se lee de la variable de entorno FLOODHUB_API_KEY (o de un archivo .env en la
raíz del proyecto, que está en .gitignore) y viaja en una cabecera, nunca en la URL,
para que no quede en logs ni en los JSON guardados.

Uso:
    .venv/bin/python tools/floodhub_extract.py            # Melissa (oct-2025) + estado actual
    .venv/bin/python tools/floodhub_extract.py --probe    # solo comprueba que la key funciona
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests

BASE = "https://floodforecasting.googleapis.com/v1"
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "floodhub"

# Países que tocó Melissa. Códigos CLDR, como pide la API.
REGIONS = ["JM", "HT", "DO", "CU"]
# La API guarda estados históricos desde 2025-08-01. Melissa tocó tierra en Jamaica
# el 28-oct-2025; pedimos el estado tal como estaba en el pico del evento.
MELISSA_CUTOFF = "2025-10-29T12:00:00Z"
MELISSA_FORECASTS = ("2025-10-24T00:00:00Z", "2025-11-02T00:00:00Z")


def api_key() -> str:
    key = os.environ.get("FLOODHUB_API_KEY")
    env = ROOT / ".env"
    if not key and env.exists():
        for line in env.read_text().splitlines():
            if line.startswith("FLOODHUB_API_KEY="):
                key = line.split("=", 1)[1].strip().strip('"')
    if not key:
        sys.exit("Falta FLOODHUB_API_KEY (variable de entorno o .env en la raíz).")
    return key


class Flood:
    def __init__(self, key: str):
        self.s = requests.Session()
        self.s.headers["X-Goog-Api-Key"] = key

    def post(self, path: str, body: dict) -> dict:
        r = self.s.post(f"{BASE}/{path}", json=body, timeout=60)
        r.raise_for_status()
        return r.json()

    def get(self, path: str, params: list[tuple[str, str]]) -> dict:
        r = self.s.get(f"{BASE}/{path}", params=params, timeout=60)
        r.raise_for_status()
        return r.json()

    def paged(self, path: str, body: dict, field: str) -> list:
        items, token = [], None
        while True:
            page = self.post(path, {**body, **({"pageToken": token} if token else {})})
            items += page.get(field, [])
            token = page.get("nextPageToken")
            if not token:
                return items


def save(name: str, data) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / name
    path.write_text(json.dumps(data, ensure_ascii=False, indent=1))
    n = len(data) if isinstance(data, list) else len(data.get("items", data))
    print(f"  {path.relative_to(ROOT)}  ({n} registros)")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--probe", action="store_true")
    args = ap.parse_args()
    f = Flood(api_key())

    if args.probe:
        g = f.post("gauges:searchGaugesByArea", {"regionCode": "JM", "pageSize": 5})
        print(json.dumps(g, ensure_ascii=False, indent=1)[:2000])
        return

    meta = {
        "fuente": "Google Flood Forecasting API (Flood Hub), uso no comercial",
        "extraido": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "regiones": REGIONS,
        "melissa_cutoff": MELISSA_CUTOFF,
    }
    gauges, status_melissa, status_now = [], [], []
    for rc in REGIONS:
        print(rc)
        gauges += f.paged("gauges:searchGaugesByArea",
                          {"regionCode": rc, "includeNonQualityVerified": True}, "gauges")
        status_melissa += f.paged("floodStatus:searchLatestFloodStatusByArea",
                                  {"regionCode": rc, "cutoffTime": MELISSA_CUTOFF,
                                   "includeNonQualityVerified": True}, "floodStatuses")
        status_now += f.paged("floodStatus:searchLatestFloodStatusByArea",
                              {"regionCode": rc, "includeNonQualityVerified": True}, "floodStatuses")
    save("gauges.json", gauges)
    save("status_melissa.json", status_melissa)
    save("status_actual.json", status_now)

    # Pronósticos emitidos durante Melissa, solo para los medidores con estado en el evento.
    ids = sorted({s["gaugeId"] for s in status_melissa if "gaugeId" in s})[:500]
    if ids:
        start, end = MELISSA_FORECASTS
        fc = f.get("gauges:queryGaugeForecasts",
                   [("gaugeIds", i) for i in ids] + [("issuedTimeStart", start), ("issuedTimeEnd", end)])
        save("forecasts_melissa.json", fc.get("forecasts", {}))
        models = f.get("gaugeModels:batchGet", [("names", f"gaugeModels/{i}") for i in ids[:100]])
        save("gauge_models.json", models.get("gaugeModels", []))

    save("significant_events.json", f.paged("significantEvents:search", {"pageSize": 1000}, "significantEvents"))
    save("meta.json", meta)


if __name__ == "__main__":
    main()
