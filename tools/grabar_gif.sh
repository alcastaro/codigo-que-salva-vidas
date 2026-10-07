#!/bin/zsh
# Graba un GIF de una plataforma: tools/grabar_gif.sh <nombre> <url> <espera_ms> <acciones.js> [segundos]
# acciones.js es una función `async page => {...}` que mueve el mapa mientras se graba.
set -eu
OUT="${0:A:h}/../deck/capturas"
mkdir -p "$OUT"
n=$1 url=$2 espera=$3 acciones=$4
S=(-s=cap)
playwright-cli $S goto "$url" >/dev/null 2>&1
playwright-cli $S run-code "async page => await page.waitForTimeout($espera)" >/dev/null 2>&1
playwright-cli $S video-start "$OUT/$n.webm" --size=1600x900 --fps=15 >/dev/null 2>&1
playwright-cli $S run-code --filename="$acciones" >/dev/null 2>&1
playwright-cli $S video-stop >/dev/null 2>&1
# GIF: 12 fps, 960 px, paleta propia (sin bandas de color)
ffmpeg -y -loglevel error -i "$OUT/$n.webm" -vf "${CROP:+crop=$CROP,}fps=${FPS:-10},scale=${ANCHO:-800}:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=128[p];[b][p]paletteuse=dither=bayer:bayer_scale=4" "$OUT/$n.gif"
rm -f "$OUT/$n.webm"
echo "$n.gif $(du -h "$OUT/$n.gif" | cut -f1)"
