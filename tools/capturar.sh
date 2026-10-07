#!/bin/zsh
# Capturas estáticas de las plataformas para el deck (1600×900).
#   tools/capturar.sh               → todas
#   tools/capturar.sh floodhub      → solo una
# Requiere una sesión abierta: playwright-cli -s=cap open --browser=chrome && playwright-cli -s=cap resize 1600 900
set -u
OUT="${0:A:h}/../deck/capturas"
mkdir -p "$OUT"
S=(-s=cap)

typeset -A URL ESPERA
URL[crisis]="https://crisisresilience.google/";                         ESPERA[crisis]=5000
URL[floodhub]="https://sites.research.google/floods/l/18.0/-77.5/7";    ESPERA[floodhub]=12000
URL[weathernext]="https://deepmind.google/science/weathernext/";        ESPERA[weathernext]=6000
URL[weatherlab]="https://deepmind.google.com/science/weatherlab";       ESPERA[weatherlab]=15000
URL[alphaearth]="https://deepmind.google/blog/alphaearth-foundations-helps-map-our-planet-in-unprecedented-detail/"; ESPERA[alphaearth]=6000
URL[ee_catalogo]="https://developers.google.com/earth-engine/datasets/catalog/GOOGLE_SATELLITE_EMBEDDING_V1_ANNUAL"; ESPERA[ee_catalogo]=6000
URL[earthengine]="https://earthengine.google.com/";                     ESPERA[earthengine]=6000
URL[timelapse]="https://earthengine.google.com/timelapse/";             ESPERA[timelapse]=12000
URL[googleearth]="https://earth.google.com/web/@18.03,-77.85,500a,20000d,35y,0h,0t,0r"; ESPERA[googleearth]=20000
URL[earthai]="https://research.google/blog/google-earth-ai-unlocking-geospatial-insights-with-foundation-models-and-cross-modal-reasoning/"; ESPERA[earthai]=6000
URL[amw]="https://amazonminingwatch.org/";                              ESPERA[amw]=15000
URL[sismos]="https://crisisresponse.google/android-alerts/";            ESPERA[sismos]=6000
URL[climateengine]="https://climateengine.org/";                         ESPERA[climateengine]=6000
URL[gemma4good]="https://blog.google/innovation-and-ai/technology/developers-tools/winning-entries-gemma-4-good-challenge/"; ESPERA[gemma4good]=6000

for k in ${@:-${(k)URL}}; do
  playwright-cli $S goto "${URL[$k]}" >/dev/null 2>&1
  playwright-cli $S run-code "async page => await page.waitForTimeout(${ESPERA[$k]})" >/dev/null 2>&1
  playwright-cli $S screenshot --filename="$OUT/$k.png" >/dev/null 2>&1
  echo "$k → $(playwright-cli $S --raw eval 'location.href' 2>/dev/null | tail -1)"
done
