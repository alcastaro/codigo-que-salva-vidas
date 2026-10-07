"""Guarda una copia (int8, comprimida) de los embeddings de AlphaEarth de la zona del taller."""
import sys, time
sys.path.insert(0, "taller")
import ayuda
LAT, LON, KM, ANCHO = 18.04, -77.82, 10, 400
bbox = ayuda.caja(LAT, LON, KM)
for anio in (2024,):
    t = time.time()
    e = ayuda.embeddings_alphaearth(bbox, anio, ANCHO)
    ayuda.guardar_embeddings(e, f"data/alphaearth/black_river_{anio}.npz")
    print(anio, e.shape, "%.0fs" % (time.time() - t))
