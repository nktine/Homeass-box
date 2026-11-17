#!/usr/bin/env python3
"""Rendus ombres deux tons (style produit) : python3 render.py -> preview/*.png"""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import trimesh
import importlib.util

os.makedirs("preview", exist_ok=True)
LIGHT = np.array([0.35, 0.45, 0.85]); LIGHT /= np.linalg.norm(LIGHT)
C = dict(base=(0.90, 0.90, 0.92), plateau=(0.12, 0.12, 0.14), diffu=(0.98, 0.98, 1.0),
         pcb=(0.10, 0.55, 0.25), cooler=(0.62, 0.64, 0.68), voice=(0.93, 0.93, 0.95))


def shaded(mesh, rgb, alpha=1.0):
    n = mesh.face_normals
    i = 0.42 + 0.58 * np.clip(n @ LIGHT, 0, 1)
    cols = [(*np.clip(np.array(rgb) * v, 0, 1), alpha) for v in i]
    return Poly3DCollection(mesh.triangles, facecolors=cols, edgecolors=(0, 0, 0, 0.05), linewidths=0.12)


def render(parts, name, elev, azim, zoom=None, figsize=(11, 8)):
    fig = plt.figure(figsize=figsize, dpi=130)
    ax = fig.add_subplot(111, projection="3d")
    for mesh, rgb, alpha in parts:
        ax.add_collection3d(shaded(mesh, rgb, alpha))
    allb = np.array([mm.bounds for mm, _, _ in parts])
    lo = allb[:, 0, :].min(axis=0); hi = allb[:, 1, :].max(axis=0)
    c = (lo + hi) / 2
    if zoom is None:
        r = (hi - lo).max() / 2 * 1.05
        ax.set_xlim(c[0] - r, c[0] + r); ax.set_ylim(c[1] - r, c[1] + r)
        ax.set_zlim(lo[2], hi[2] + r * 0.55); ax.set_box_aspect((1, 1, 0.55))
    else:
        ax.set_xlim(zoom[0], zoom[1]); ax.set_ylim(zoom[2], zoom[3]); ax.set_zlim(zoom[4], zoom[5])
        ax.set_box_aspect((zoom[1]-zoom[0], zoom[3]-zoom[2], zoom[5]-zoom[4]))
    ax.view_init(elev=elev, azim=azim); ax.set_axis_off()
    fig.savefig(f"preview/{name}.png", bbox_inches="tight", pad_inches=0.04, facecolor="white")
    plt.close(fig)


spec = importlib.util.spec_from_file_location("m", "boitier_pi5_voice.py")
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
base = trimesh.load("out/base.stl", process=True)
plate = trimesh.load("out/plateau.stl", process=True)
dif = trimesh.load("out/diffuseur.stl", process=True)
pcb, cooler, voice = m.ghosts()

asm = [(base, C["base"], 1), (plate, C["plateau"], 1), (dif, C["diffu"], 0.8)]
ghost = asm + [(pcb, C["pcb"], 0.9), (cooler, C["cooler"], 0.95), (voice, C["voice"], 0.92)]

render(ghost, "v3_iso", 22, -58)
render(ghost, "v3_iso2", 18, 125)
render(ghost, "v3_dessus", 75, -90)
render(asm, "v3_avant", 5, -90)
render(asm, "v3_droite", 7, -10)
render(asm, "v3_arriere", 9, 95)
render([(base, C["base"], 1)], "v3_base_dessous", -75, -90)
render([(plate, C["plateau"], 1)], "v3_plateau_dessus", 65, -90)
render([(plate, C["plateau"], 1)], "v3_plateau_iso", 28, -55)
render(asm, "v3_zoom_facade", 4, -90, zoom=(-5, 121, -14, 12, 0, 33))
render(asm, "v3_zoom_dessus", 55, -80, zoom=(-5, 121, -5, 105, 28, 60))
render(ghost, "v3_zoom_interieur", 35, -125, zoom=(0, 116, 0, 100, 0, 40))
print("ok ->", sorted(os.listdir("preview")))
