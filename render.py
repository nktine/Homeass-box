#!/usr/bin/env python3
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import trimesh

os.makedirs("preview", exist_ok=True)

VIEWS = {
    "iso":      ([35, -55], 0.9),
    "dessus":   ([89, -90], 1.0),
    "avant":    ([0, -90], 1.0),
    "droite":   ([0, 0], 1.0),
    "gauche":   ([0, 180], 1.0),
    "arriere":  ([0, 90], 1.0),
    "dessous":  ([-89, -90], 1.0),
    "iso2":     ([-30, 125], 0.9),
}


def render(mesh, name, elev, azim, scale, color):
    fig = plt.figure(figsize=(11, 8), dpi=110)
    ax = fig.add_subplot(111, projection="3d")
    tris = mesh.triangles
    pc = Poly3DCollection(tris, alpha=1.0, facecolor=color, edgecolor=(0, 0, 0, 0.06), linewidths=0.15)
    ax.add_collection3d(pc)
    b = mesh.bounds
    c = (b[0] + b[1]) / 2
    r = (b[1] - b[0]).max() / 2 * scale
    ax.set_xlim(c[0] - r, c[0] + r)
    ax.set_ylim(c[1] - r, c[1] + r)
    ax.set_zlim(max(0, c[2] - r), c[2] + r)
    ax.set_box_aspect((1, 1, 0.45))
    ax.view_init(elev=elev, azim=azim)
    ax.set_axis_off()
    fig.savefig(f"preview/{name}.png", bbox_inches="tight", pad_inches=0.05)
    plt.close(fig)


base = trimesh.load("out/base.stl")
lid = trimesh.load("out/couvercle.stl")
asm = trimesh.load("out/apercu.stl")

for name, (elev, azim), scale in [(k, (v[0][0], v[0][1]), v[1]) for k, v in VIEWS.items()]:
    render(asm, f"apercu_{name}", elev, azim, scale, "0.75")
    render(base, f"base_{name}", elev, azim, scale, "0.55")
render(lid, "couvercle_dessus", 89, -90, 1.0, "0.35")
render(lid, "couvercle_dessous", -89, -90, 1.0, "0.35")
render(lid, "couvercle_iso", 30, -60, 0.9, "0.35")
print("previews ->", sorted(os.listdir("preview")))
