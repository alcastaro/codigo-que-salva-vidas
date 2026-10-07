"""Lanza la plataforma de la Pista D en local (sin enlace público) para probarla con el navegador."""
import sys
sys.path.insert(0, "taller")
import plataforma as pf
pf.app(copias={"Constanza (laderas agrícolas)": "data/alphaearth/constanza_serie.npz"}, compartir=False)
