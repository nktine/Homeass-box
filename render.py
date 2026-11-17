#!/usr/bin/env python3
"""Rendus studio blancs (v5) : python3 render.py -> preview/*.png"""
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
C = dict(base=(0.93, 0.93, 0.95), plateau=(0.97, 0.97, 0.99), diffu=(1.0, 1.0, 1.0),
         pcb=(0.10, 0.55, 0.25), cooler=(0.60, 0.62, 0.66), voice=(0.16, 0.16, 0.18))


def shaded(mesh, rgb, alpha=1.0):
    n = mesh.face_normals
    i = 0.45 + 0.55 * np.clip(n @ LIGHT, 0, 1)
    cols = [(*np.clip(np.array(rgb) * v, 0, 1), alpha) for v in i]
    return Poly3DCollection(mesh.triangles, facecolors=cols, edgecolors=(0.1, 0.1, 0.1, 0.08), linewidths=0.1)


def render(parts, name, elev, azim, zoom=None, figsize=(11, 8)):
    fig = plt.figure(figsize=figsize, dpi=140)
    ax = fig.add_subplot(111, projection="3d")
    for mesh, rgb, alpha in parts:
        ax.add_collection3d(shaded(mesh, rgb, alpha))
    allb = np.array([mm.bounds for mm, _, _ in parts])
    lo = allb[:, 0, :].min(axis=0); hi = allb[:, 1, :].max(axis=0)
    c = (lo + hi) / 2
    if zoom is None:
        r = (hi - lo).max() / 2 * 1.04
        ax.set_xlim(c[0] - r, c[0] + r); ax.set_ylim(c[1] - r, c[1] + r)
        ax.set_zlim(lo[2], hi[2] + r * 0.35); ax.set_box_aspect((1, 1, 0.5))
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

asm = [(base, C["base"], 1), (plate, C["plateau"], 1), (dif, C["diffu"], 0.75)]
ghost = asm + [(pcb, C["pcb"], 0.92), (cooler, C["cooler"], 0.95), (voice, C["voice"], 0.94)]

render(ghost, "v5_hero", 16, -62)                 # 3/4 haut, coin visible
render(ghost, "v5_hero2", 14, 118)
render(asm, "v5_profil", 4, 0)                    # profil lateral : le coin se voit
render(asm, "v5_profil_arriere", 6, 180)
render(asm, "v5_dessus", 72, -90)
render(asm, "v5_avant", 4, -90)
render(asm, "v5_droite", 5, -8)
render(asm, "v5_arriere", 6, 92)
render([(base, C["base"], 1)], "v5_base_dessous", -72, -90)
render(ghost, "v5_zoom_dessus", 48, -78, zoom=(85, 195, -5, 109, 24, 47))
render(ghost, "v5_zoom_voice", 30, -125, zoom=(-5, 100, -5, 109, 0, 47))
render(asm, "v5_zoom_facade", 3, -90, zoom=(85, 195, -16, 10, 0, 40))
render(asm, "v5_zoom_droite", 4, -6, zoom=(150, 196, -6, 110, 0, 40))
print("ok ->", sorted(os.listdir("preview")))
