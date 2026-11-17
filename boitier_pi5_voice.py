#!/usr/bin/env python3
"""Boitier hub Home Assistant (Pi 5 + Active Cooler + Voice PE) - v2 style premium.

Style "appareil consumer" : silhouette organique (coins R16, chanfrein du rebord),
couvercle en deux tons avec jeu d'ombre (reveal), vis cachees par le dessous,
bandeau LED en base de la face avant (diffuseur translucide), logo maison grave,
grilles haut-parleur en micro-perforations (facon tissu), pieds caoutchouc encastres.

Cotes Pi 5 issues du modele de reference officiel RP-004882-DD (z=0 = dessus PCB) :
  USB x4 (bord x=85) y 22.30..54.66 z -3.50..16.78 ; Ethernet y 2.25..18.15 z -2.05..13.70 ;
  USB-C (y=0) x 6.73..15.67 ; micro-HDMI x 22.55..29.05 et 35.95..42.45 ; microSD bord x=0.
  Trous M2.5 : rectangle 58 x 49 mm. Active Cooler : 13.7 mm au-dessus du PCB.

Usage : pip install trimesh manifold3d shapely matplotlib
         python3 boitier_pi5_voice.py   -> out/{base,couvercle,lightbar,apercu}.stl
"""

import math
import os

import numpy as np
import trimesh
from shapely.geometry import Polygon, box

P = dict(
    wall=3.0, floor=3.0, h_int=26.0,
    r_out=16.0, chamfer=1.0,          # rayon exterieur + chanfrein du rebord superieur
    lid_t=3.5, lid_reveal=0.8, lid_chamfer=1.5,
    px0=94.0, px1=186.0, py0=3.0, py1=91.0,   # baie Pi (interieur)
    vx0=3.0, vx1=91.0, vy0=3.0, vy1=91.0,     # baie Voice (interieur)
    bx=97.0, by=7.0,
    standoff_h=6.0, standoff_d=6.0, hole_m25=2.2,
    post_d=8.0, hole_m3=4.0, floor_screw_d=3.4,
    play=0.5,
    extrusion=20,
    rail_len=(100.0, 185.0), rail_protrude=6.5, bolt_x=(115.0, 170.0), bolt_d=5.5,
    hex_af=4.0, hex_dx=5.5, hex_dy=4.763,
    vent=(104.0, 176.0, 13.0, 81.0),
    spk_hole_d=1.8, spk_pitch=3.2, spk_win=(10.0, 81.0, 6.0, 23.0),  # x/y range, z range
    lightbar=(102.0, 142.0, 4.0, 7.5),     # x0,x1,z0,z1 fente LED face avant
    logo_cx=47.0, logo_z0=22.0, logo_w=13.0, logo_h=6.5, logo_depth=0.7,
    gpio_slot=False,
    outdir="out",
)

OUT_X, OUT_Y = 189.0, 94.0
BASE_H = P["floor"] + P["h_int"]           # 29
LID_Z0, LID_Z1 = BASE_H, BASE_H + P["lid_t"]
BX, BY = P["bx"], P["by"]
PCB_BOT = P["floor"] + P["standoff_h"]
PCB_TOP = PCB_BOT + 1.6


def zc(z_board):
    return PCB_TOP + z_board


def rounded_rect_pts(x0, y0, x1, y1, r, n=8):
    pts = []
    for cx, cy, a0 in [(x1 - r, y1 - r, 0), (x0 + r, y1 - r, 90),
                       (x0 + r, y0 + r, 180), (x1 - r, y0 + r, 270)]:
        for i in range(n + 1):
            a = math.radians(a0 + 90.0 * i / n)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def extrude_pts(pts, z0, z1):
    return trimesh.creation.extrude_polygon(Polygon(pts), z1 - z0).apply_translation([0, 0, z0])


def loft(pts_a, z_a, pts_b, z_b):
    n = len(pts_a)
    verts = [[x, y, z_a] for x, y in pts_a] + [[x, y, z_b] for x, y in pts_b]
    faces = []
    for i in range(n):
        j = (i + 1) % n
        faces.append([i, j, n + j])
        faces.append([i, n + j, n + i])
    for i in range(1, n - 1):
        faces.append([0, i + 1, i])
        faces.append([n, n + i, n + i + 1])
    m = trimesh.Trimesh(vertices=verts, faces=faces, process=True)
    m.fix_normals()
    return m


def mbox(x0, y0, z0, x1, y1, z1):
    return trimesh.creation.box(bounds=[[x0, y0, z0], [x1, y1, z1]])


def mcyl(x, y, z0, z1, r, sections=32):
    m = trimesh.creation.cylinder(radius=r, height=z1 - z0, sections=sections)
    m.apply_translation([x, y, (z0 + z1) / 2])
    return m


def hex_prism(x, y, z0, z1, af):
    r = af / math.sqrt(3.0)
    pts = [(x + r * math.cos(math.radians(60 * i)), y + r * math.sin(math.radians(60 * i)))
           for i in range(6)]
    return extrude_pts(pts, z0, z1)


def cyl_y(x, y0, z, r, length, sections=32):
    m = trimesh.creation.cylinder(radius=r, height=length, sections=sections)
    m.apply_transform(trimesh.transformations.rotation_matrix(math.pi / 2, [1, 0, 0]))
    m.apply_translation([x, y0 + length / 2, z])
    return m


def union(meshes):
    return trimesh.boolean.union(meshes, engine="manifold")


def diff(a, meshes):
    return trimesh.boolean.difference([a] + list(meshes), engine="manifold")


def cut_wall_x(s, x0, x1, y0, y1, z0, z1):
    return diff(s, [mbox(x0 - 1, y0, z0, x1 + 1, y1, z1)])


def cut_wall_y(s, y0, y1, x0, x1, z0, z1):
    return diff(s, [mbox(x0, y0 - 1, z0, x1, y1 + 1, z1)])


POSTS = [(98, 7), (182, 7), (98, 87), (182, 87)]


def build_base():
    p = P
    r, ch = p["r_out"], p["chamfer"]
    outer = extrude_pts(rounded_rect_pts(0, 0, OUT_X, OUT_Y, r), 0, BASE_H - ch)
    outer = union([outer, loft(rounded_rect_pts(0, 0, OUT_X, OUT_Y, r), BASE_H - ch,
                                 rounded_rect_pts(ch, ch, OUT_X - ch, OUT_Y - ch, r - ch), BASE_H)])
    base = outer
    base = diff(base, [
        mbox(p["vx0"], p["vy0"], p["floor"], p["vx1"], p["vy1"], BASE_H + 1),
        mbox(p["px0"], p["py0"], p["floor"], p["px1"], p["py1"], BASE_H + 1),
    ])
    holes = (p["bx"] + 13.5, p["bx"] + 71.5)
    vows = (p["by"] + 3.5, p["by"] + 52.5)
    st = [mcyl(x, y, p["floor"], p["floor"] + p["standoff_h"], p["standoff_d"] / 2)
          for x in holes for y in vows]
    base = union([base] + st)
    base = diff(base, [mcyl(x, y, p["floor"] - 1, p["floor"] + p["standoff_h"] + 1, p["hole_m25"] / 2)
                       for x in holes for y in vows])
    # trous de vis du couvercle (vis M3 par le dessous)
    base = diff(base, [mcyl(x, y, -1, p["floor"] + 1, p["floor_screw_d"] / 2) for x, y in POSTS])
    # ergots de maintien Voice
    lip_top = p["floor"] + 21.0
    for cx, cy in [(p["vx0"], p["vy0"]), (p["vx1"] - 12, p["vy0"]),
                   (p["vx0"], p["vy1"] - 12), (p["vx1"] - 12, p["vy1"] - 12)]:
        base = union([base, mbox(cx, cy, lip_top, cx + 12, cy + 12, BASE_H)])

    # ports mur droit
    eth = (BY + 2.25 - p["play"], BY + 18.15 + p["play"])
    usb = (BY + 22.30 - p["play"], BY + 54.66 + p["play"])
    base = cut_wall_x(base, p["px1"], OUT_X, eth[0], eth[1], zc(-2.05) - p["play"], zc(13.70) + p["play"])
    base = cut_wall_x(base, p["px1"], OUT_X, usb[0], usb[1], zc(-3.50) - p["play"], zc(16.78) + p["play"])
    # ports mur avant
    usbc = (BX + 6.73 - p["play"], BX + 15.67 + p["play"])
    base = cut_wall_y(base, 0, p["py0"], usbc[0], usbc[1], zc(-0.80) - p["play"], zc(3.16) + p["play"])
    for hx in (BX + 22.55, BX + 35.95):
        base = cut_wall_y(base, 0, p["py0"], hx - 3.25 - p["play"], hx + 3.25 + p["play"],
                          zc(-0.55) - p["play"], zc(2.97) + p["play"])
    # fente bandeau LED (traversee, diffuseur rapporte)
    lb = p["lightbar"]
    base = cut_wall_y(base, 0, p["wall"], lb[0], lb[1], lb[2], lb[3])
    # logo maison grave (face avant, au-dessus de la baie Voice) - prismes en plan X-Z
    cx, z0, w, h, d = p["logo_cx"], p["logo_z0"], p["logo_w"], p["logo_h"], p["logo_depth"]
    body = [(cx - w / 2, z0), (cx + w / 2, z0), (cx + w / 2, z0 + h), (cx - w / 2, z0 + h)]
    roof = [(cx - w / 2 - 0.8, z0 + h), (cx + w / 2 + 0.8, z0 + h), (cx, z0 + h + p["logo_h"])]

    def prism_xz(pts, y0, y1):
        n = len(pts)
        verts = [[x, y0, z] for x, z in pts] + [[x, y1, z] for x, z in pts]
        faces = []
        for i in range(n):
            j = (i + 1) % n
            faces += [[i, j, n + j], [i, n + j, n + i]]
        for i in range(1, n - 1):
            faces += [[0, i + 1, i], [n, n + i, n + i + 1]]
        m = trimesh.Trimesh(vertices=verts, faces=faces, process=True)
        m.fix_normals()
        return m

    logo = union([prism_xz(body, -0.1, d), prism_xz(roof, -0.1, d)])
    base = diff(base, [logo])

    # cloison : reliefs cote carte + passage USB-C Voice
    base = cut_wall_x(base, p["vx1"], p["px0"], 4.0, 45.0, zc(-3.5) - 0.5, zc(3.5) + 1.0)
    base = cut_wall_x(base, p["vx1"], p["px0"], 50.0, 66.0, p["floor"], p["floor"] + 8.0)
    # mur arriere : sortie cables + entrees d'air
    base = cut_wall_y(base, p["py1"], OUT_Y, 135.0, 160.0, 5.0, 13.0)
    for x0, x1 in [(100.0, 130.0), (165.0, 180.0)]:
        z = 5.0
        while z + 2.2 <= 14.0:
            base = cut_wall_y(base, p["py1"], OUT_Y, x0, x1, z, z + 2.2)
            z += 3.4
    # micro-perforations haut-parleur Voice (avant, gauche, arriere)
    a0, a1, z0, z1 = p["spk_win"]
    d, pitch = p["spk_hole_d"], p["spk_pitch"]
    perfs = []
    a = a0 + d / 2
    while a <= a1 - d / 2:
        z = z0 + d / 2
        while z <= z1 - d / 2:
            perfs.append(cyl_y(a, -1.0, z, d / 2, p["wall"] + 2))                  # avant
            perfs.append(cyl_y(a, p["vy1"] - p["wall"] + 1.0, z, d / 2, p["wall"] + 2))  # arriere
            px = trimesh.creation.cylinder(radius=d / 2, height=p["wall"] + 2, sections=24)
            px.apply_transform(trimesh.transformations.rotation_matrix(math.pi / 2, [0, 1, 0]))
            px.apply_translation([1.5, a, z])
            perfs.append(px)
            z += pitch
        a += pitch
    base = diff(base, perfs)
    # fentes fond + colliers + pieds encastres
    for x0 in (118.0, 128.0, 138.0, 148.0, 158.0):
        base = diff(base, [mbox(x0, 14.0, -1, x0 + 4.0, 56.0, p["floor"] + 1)])
    for x0 in (125.0, 150.0):
        base = diff(base, [mbox(x0, 68.0, -1, x0 + 5.0, 86.0, p["floor"] + 1)])
    for fx, fy in [(14, 14), (OUT_X - 14, 14), (14, OUT_Y - 14), (OUT_X - 14, OUT_Y - 14)]:
        base = diff(base, [mcyl(fx, fy, -1, 1.5, 6.0)])
    # rail profil alu + boulons M5 + serrures
    slot_w = 5.6 if p["extrusion"] == 20 else 7.6
    rz0, rz1 = 16.4 - slot_w / 2, 16.4 + slot_w / 2
    base = union([base, mbox(p["rail_len"][0], OUT_Y, rz0, p["rail_len"][1], OUT_Y + p["rail_protrude"], rz1)])
    for bx_ in p["bolt_x"]:
        base = diff(base, [cyl_y(bx_, OUT_Y - 1, 16.4, p["bolt_d"] / 2, p["rail_protrude"] + p["wall"] + 2)])
        base = diff(base, [cyl_y(bx_, OUT_Y - p["wall"] / 2, 24.0, 3.5, p["wall"] + 2)])
        base = diff(base, [mbox(bx_ - 1.75, OUT_Y - p["wall"] - 1, 18.0, bx_ + 1.75, OUT_Y + 1, 24.0)])
    return base


def build_lid():
    p = P
    rv, lc = p["lid_reveal"], p["lid_chamfer"]
    x0, y0, x1, y1 = p["vx1"] + rv, rv, OUT_X - rv - 0.6, OUT_Y - rv - 0.2
    r = p["r_out"] - 2
    lid = loft(rounded_rect_pts(x0 + 0.6, y0 + 0.6, x1 - 0.6, y1 - 0.6, r - 0.6), LID_Z0,
               rounded_rect_pts(x0, y0, x1, y1, r), LID_Z0 + 0.6)
    lid = union([lid, extrude_pts(rounded_rect_pts(x0, y0, x1, y1, r), LID_Z0 + 0.6, LID_Z1 - lc)])
    lid = union([lid, loft(rounded_rect_pts(x0, y0, x1, y1, r), LID_Z1 - lc,
                            rounded_rect_pts(x0 + lc, y0 + lc, x1 - lc, y1 - lc, r - lc), LID_Z1)])
    # honeycomb fin
    af, dx, dy = p["hex_af"], p["hex_dx"], p["hex_dy"]
    x0v, x1v, y0v, y1v = p["vent"]
    hexes, row, y = [], 0, y0v + dy / 2
    while y <= y1v:
        off = dx / 2 if row % 2 else 0.0
        x = x0v + off + dx / 2
        while x <= x1v:
            hexes.append(hex_prism(x, y, LID_Z0 - 1, LID_Z1 + 1, af))
            x += dx
        y += dy
        row += 1
    lid = diff(lid, hexes)
    # 4 plots sous le couvercle (vis M3 par le dessous)
    lid = union([lid] + [mcyl(x, y, LID_Z0 - 6, LID_Z0 + 0.5, p["post_d"] / 2) for x, y in POSTS])
    lid = diff(lid, [mcyl(x, y, LID_Z0 - 7, LID_Z0 + 1, p["hole_m3"] / 2) for x, y in POSTS])
    if p["gpio_slot"]:
        lid = diff(lid, [mbox(BX + 2.5, 61.0, LID_Z0 - 1, BX + 55.5, 67.0, LID_Z1 + 1)])
    return lid


def build_lightbar():
    lb = P["lightbar"]
    return mbox(lb[0], 0.6, lb[2], lb[1], 2.6, lb[3])


def ghosts():
    return [
        mbox(BX, BY, PCB_BOT, BX + 85, BY + 56, PCB_TOP),
        mbox(BX + 20, BY + 8, PCB_TOP, BX + 70, BY + 48, PCB_TOP + 13.7),
        mbox(5, 5, P["floor"], 89, 89, P["floor"] + 21),
    ]


def main():
    os.makedirs(P["outdir"], exist_ok=True)
    base = build_base()
    lid = build_lid()
    bar = build_lightbar()
    for name, m in [("base", base), ("couvercle", lid), ("lightbar", bar)]:
        m.export(os.path.join(P["outdir"], f"{name}.stl"))
        print(f"{name}: watertight={m.is_watertight} volume={m.volume:.0f} mm3 "
              f"bbox={m.bounds[0].round(1)}..{m.bounds[1].round(1)}")
    asm = union([base, lid, bar] + ghosts())
    asm.export(os.path.join(P["outdir"], "apercu.stl"))
    solid = union([base, lid])
    for nm, g in [("cooler", ghosts()[1]), ("voice", ghosts()[2])]:
        inter = trimesh.boolean.intersection([solid, g], engine="manifold")
        print(f"interference {nm}: {inter.volume:.1f} mm3 (doit etre ~0)")
    print("OK ->", P["outdir"])


if __name__ == "__main__":
    main()
