#!/usr/bin/env python3
"""Homeass-box v5 "plaque en coin blanche" - boitier hub facon Home Assistant Voice PE.

Plaque 190 x 104 mm, coins R28, dessus INCLINE (33 mm devant -> 45 mm arriere, ~7 degres) :
corps 100% blanc, anneau LED qui suit la pente sur 3 cotes (diffuseur translucide),
logo maison grave sur le dessus, Voice PE (84x84x21) posee a fleur sur un socle incline,
Pi 5 + Active Cooler dans la baie gauche. Fixation profile 2020/2040 arriere,
vis par le dessous, 4 pieds encastres, aucun support a l'impression.

Cotes Pi 5 (modele de reference officiel RP-004882-DD, z=0 = dessus PCB) :
  USB x4 (bord x=85) y 22.30..54.66 z -3.50..16.78 ; Ethernet y 2.25..18.15 z -2.05..13.70 ;
  USB-C (y=0) x 6.73..15.67 ; micro-HDMI x 22.55..29.05 et 35.95..42.45 ; microSD bord x=0.
  Trous M2.5 : rectangle 58 x 49 mm. Active Cooler : 13.7 mm au-dessus du PCB.

Usage : pip install trimesh manifold3d shapely matplotlib
         python3 boitier_pi5_voice.py  -> out/{base,plateau,diffuseur,apercu}.stl
"""

import math
import os

import numpy as np
import trimesh
from shapely.geometry import Polygon

P = dict(
    ox=190.0, oy=104.0, r_out=28.0, wall=3.0, floor=3.0,
    h_front=33.0, h_back=45.0,          # dessus incline (coin)
    cav_top=29.6,                        # plafond plat de la baie Pi
    plate_t=3.0, seat=1.4,
    bx=97.0, by=7.0, standoff_h=6.0, standoff_d=6.0, hole_m25=2.2,
    post_d=8.0, hole_m3=4.0, floor_screw_d=3.4,
    play=0.5,
    extrusion=20, rail=(40.0, 160.0), rail_protrude=6.5,
    bolt_x=(60.0, 140.0), bolt_d=5.5,
    led_band=(-4.2, -1.8),               # bande LED relative au dessus (suivant la pente)
    vent_af=3.5, vent_dx=4.8, vent_dy=4.157, vent=(100.0, 180.0, 8.0, 96.0),
    logo=dict(cx=140.0, cy=50.0, w=18.0, h=9.0, roof=4.0, depth=0.5),
    voice=dict(w=84.0, h=21.0), voice_xy=(5.0, 8.0), riser=(5.0, 6.0, 89.0, 96.0),
    cable_cut=(86.0, 90.0, 90.0, 96.0),   # puits cable Voice -> cloison (x0,x1,y0,y1)
    part_slot=(70.0, 80.0),               # fente cloison x 91..94
    spk=(8.0, 92.0, 8.0, 26.0), hole_d=1.8, pitch=3.2,
    spk_part_z=(8.0, 38.0),
    back_slats=((8.0, 40.0), (150.0, 182.0), 7.0, 15.0),
    cable_notch=(110.0, 140.0, 7.0, 14.0),
    gpio_slot=False,
    outdir="out",
)

OX, OY = P["ox"], P["oy"]
BX, BY = P["bx"], P["by"]
PCB_BOT = P["floor"] + P["standoff_h"]
PCB_TOP = PCB_BOT + 1.6
POSTS = ((97.5, 8.0), (182.5, 8.0), (97.5, 96.0), (182.5, 96.0))


def zshell(y):
    return P["h_front"] + (P["h_back"] - P["h_front"]) * y / OY


def zc(z_board):
    return PCB_TOP + z_board


def rounded_rect_pts(x0, y0, x1, y1, r, n=10):
    pts = []
    for cx, cy, a0 in [(x1 - r, y1 - r, 0), (x0 + r, y1 - r, 90),
                       (x0 + r, y0 + r, 180), (x1 - r, y0 + r, 270)]:
        for i in range(n + 1):
            a = math.radians(a0 + 90.0 * i / n)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def extrude_pts(pts, z0, z1):
    return trimesh.creation.extrude_polygon(Polygon(pts), z1 - z0).apply_translation([0, 0, z0])


def sloped_ring(pts, zb_fn, zt_fn):
    n = len(pts)
    verts = [[x, y, zb_fn(y)] for x, y in pts] + [[x, y, zt_fn(y)] for x, y in pts]
    faces = []
    for i in range(n):
        j = (i + 1) % n
        faces += [[i, j, n + j], [i, n + j, n + i]]
    for i in range(1, n - 1):
        faces += [[0, i + 1, i], [n, n + i, n + i + 1]]
    m = trimesh.Trimesh(vertices=verts, faces=faces, process=True)
    m.fix_normals()
    return m


def sloped_box(x0, x1, y0, y1, zb_fn, zt_fn):
    pts = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    return sloped_ring(pts, zb_fn, zt_fn)


def mbox(x0, y0, z0, x1, y1, z1):
    return trimesh.creation.box(bounds=[[x0, y0, z0], [x1, y1, z1]])


def mcyl(x, y, z0, z1, r, sections=32):
    m = trimesh.creation.cylinder(radius=r, height=z1 - z0, sections=sections)
    m.apply_translation([x, y, (z0 + z1) / 2])
    return m


def cyl_y(x, y0, z, r, length, sections=24):
    m = trimesh.creation.cylinder(radius=r, height=length, sections=sections)
    m.apply_transform(trimesh.transformations.rotation_matrix(math.pi / 2, [1, 0, 0]))
    m.apply_translation([x, y0 + length / 2, z])
    return m


def cyl_x(x0, y, z, r, length, sections=24):
    m = trimesh.creation.cylinder(radius=r, height=length, sections=sections)
    m.apply_transform(trimesh.transformations.rotation_matrix(math.pi / 2, [0, 1, 0]))
    m.apply_translation([x0 + length / 2, y, z])
    return m


def hex_prism(x, y, z0, z1, af):
    r = af / math.sqrt(3.0)
    pts = [(x + r * math.cos(math.radians(60 * i)), y + r * math.sin(math.radians(60 * i)))
           for i in range(6)]
    return extrude_pts(pts, z0, z1)


def union(ms):
    return trimesh.boolean.union(ms, engine="manifold")


def diff(a, ms):
    return trimesh.boolean.difference([a] + list(ms), engine="manifold")


def cut_wall_x(s, x0, x1, y0, y1, z0, z1):
    return diff(s, [mbox(x0 - 1, y0, z0, x1 + 1, y1, z1)])


def cut_wall_y(s, y0, y1, x0, x1, z0, z1):
    return diff(s, [mbox(x0, y0 - 1, z0, x1, y1 + 1, z1)])


def build_base():
    p = P
    base = sloped_ring(rounded_rect_pts(0, 0, OX, OY, p["r_out"]), lambda y: 0.0, zshell)
    base = diff(base, [
        mbox(94, 3, p["floor"], 187, 101, p["cav_top"] + 0.5),        # baie Pi
        mbox(92, 1, p["cav_top"], 189, 103, p["cav_top"] + p["seat"] + 1),  # siege du couvercle
        mbox(3, 3, p["floor"], 91, 101, zshell(101) + 1),              # baie Voice (ouverte)
    ])
    st = [(BX + 13.5, BY + 3.5), (BX + 71.5, BY + 3.5), (BX + 13.5, BY + 52.5), (BX + 71.5, BY + 52.5)]
    base = union([base] + [mcyl(x, y, p["floor"], p["floor"] + p["standoff_h"], p["standoff_d"] / 2)
                           for x, y in st])
    base = diff(base, [mcyl(x, y, p["floor"] - 1, p["floor"] + p["standoff_h"] + 1, p["hole_m25"] / 2)
                       for x, y in st])
    base = diff(base, [mcyl(x, y, -1, p["floor"] + 1, p["floor_screw_d"] / 2) for x, y in POSTS])
    for x0 in (110.0, 120.0, 130.0, 140.0, 150.0):
        base = diff(base, [mbox(x0, 20.0, -1, x0 + 4.0, 58.0, p["floor"] + 1)])
    for x0 in (110.0, 150.0):
        base = diff(base, [mbox(x0, 70.0, -1, x0 + 5.0, 96.0, p["floor"] + 1)])
    for fx, fy in [(16, 16), (OX - 16, 16), (16, OY - 16), (OX - 16, OY - 16)]:
        base = diff(base, [mcyl(fx, fy, -1, 1.5, 6.0)])
    # socle incline de la Voice
    r = p["riser"]
    base = union([base, sloped_box(r[0], r[2], r[1], r[3], lambda y: p["floor"],
                                   lambda y: zshell(y) - p["voice"]["h"] - 1.0)])
    # puits cable Voice (traverse socle + fond au niveau cloison)
    cc = p["cable_cut"]
    base = diff(base, [mbox(cc[0], cc[2], 0, cc[1], cc[3], zshell(101) + 1)])
    base = cut_wall_x(base, 91, 94, p["part_slot"][0], p["part_slot"][1], 0, p["floor"] + 5)
    # la Voice tient dans son logement (2 mm de jeu) : pas d'ergots, formes pures
    # anneau LED suivant la pente (avant, gauche, arriere)
    b0, b1 = p["led_band"]
    base = diff(base, [sloped_box(2, OX - 2, -1, p["wall"] + 1, lambda y: zshell(y) + b0, lambda y: zshell(y) + b1),
                       sloped_box(-1, p["wall"] + 1, 2, OY - 2, lambda y: zshell(y) + b0, lambda y: zshell(y) + b1),
                       sloped_box(2, OX - 2, OY - p["wall"] - 1, OY + 1, lambda y: zshell(y) + b0, lambda y: zshell(y) + b1)])
    # ports droit (bord x=85 de la carte -> x=182, mur x=187..190)
    eth = (BY + 2.25 - p["play"], BY + 18.15 + p["play"])
    usb = (BY + 22.30 - p["play"], BY + 54.66 + p["play"])
    base = cut_wall_x(base, OX - p["wall"], OX, eth[0], eth[1], zc(-2.05) - p["play"], zc(13.70) + p["play"])
    base = cut_wall_x(base, OX - p["wall"], OX, usb[0], usb[1], zc(-3.50) - p["play"], zc(16.78) + p["play"])
    # ports avant : USB-C + 2 micro-HDMI
    usbc = (BX + 6.73 - p["play"], BX + 15.67 + p["play"])
    base = cut_wall_y(base, 0, p["wall"], usbc[0], usbc[1], zc(-0.80) - p["play"], zc(3.16) + p["play"])
    for bx_ in (22.55, 35.95):
        base = cut_wall_y(base, 0, p["wall"], BX + bx_ - 3.25 - p["play"], BX + bx_ + 3.25 + p["play"],
                          zc(-0.55) - p["play"], zc(2.97) + p["play"])
    # perforations HP Voice : gauche, avant, cloison
    a0, a1, z0, z1 = p["spk"]
    d, pitch = p["hole_d"], p["pitch"]
    perfs = []
    a = a0 + d / 2
    while a <= a1 - d / 2:
        z = z0 + d / 2
        while z <= z1 - d / 2:
            perfs.append(cyl_x(-1.0, a, z, d / 2, p["wall"] + 2))
            perfs.append(cyl_y(a, -1.0, z, d / 2, p["wall"] + 2))
            z += pitch
        a += pitch
    base = diff(base, perfs)
    pz0, pz1 = p["spk_part_z"]
    pperfs = []
    a = a0 + d / 2
    while a <= a1 - d / 2:
        z = pz0 + d / 2
        while z <= pz1 - d / 2:
            pperfs.append(cyl_x(90.0, a, z, d / 2, p["wall"] + 2))
            z += pitch
        a += pitch
    base = diff(base, pperfs)
    # arriere : encoche cables + entrees d'air + rail + M5 + serrures
    cn = p["cable_notch"]
    base = cut_wall_y(base, OY - p["wall"], OY, cn[0], cn[1], cn[2], cn[3])
    sl = p["back_slats"]
    for x0, x1 in (sl[0], sl[1]):
        z = sl[2]
        while z + 2.2 <= sl[3]:
            base = cut_wall_y(base, OY - p["wall"], OY, x0, x1, z, z + 2.2)
            z += 3.4
    slot_w = 5.6 if p["extrusion"] == 20 else 7.6
    rz0, rz1 = 16.4 - slot_w / 2, 16.4 + slot_w / 2
    base = union([base, mbox(p["rail"][0], OY, rz0, p["rail"][1], OY + p["rail_protrude"], rz1)])
    for bx_ in p["bolt_x"]:
        base = diff(base, [cyl_y(bx_, OY - p["wall"] - 1, 16.4, p["bolt_d"] / 2, p["rail_protrude"] + p["wall"] + 2)])
        base = diff(base, [cyl_y(bx_, OY - p["wall"] - 1, 20.0, 3.5, p["wall"] + 2)])
        base = diff(base, [mbox(bx_ - 1.75, OY - p["wall"] - 1, 14.0, bx_ + 1.75, OY + 1, 20.0)])
    return base


def build_plate():
    p = P
    x0, y0, x1, y1 = 92.2, 1.2, OX - 1.2, OY - 1.2
    plate = sloped_ring(rounded_rect_pts(x0, y0, x1, y1, p["r_out"] - 4),
                        lambda y: p["cav_top"], lambda y: zshell(y) - 1.0)
    af, dx, dy = p["vent_af"], p["vent_dx"], p["vent_dy"]
    x0v, x1v, y0v, y1v = p["vent"]
    hexes, row, y = [], 0, y0v + dy / 2
    while y <= y1v:
        off = dx / 2 if row % 2 else 0.0
        x = x0v + off + dx / 2
        while x <= x1v:
            if all((x - px) ** 2 + (y - py) ** 2 > 6.5 ** 2 for px, py in POSTS):
                hexes.append(hex_prism(x, y, p["cav_top"] - 1, zshell(101) + 1, af))
            x += dx
        y += dy
        row += 1
    plate = diff(plate, hexes)
    lg = p["logo"]
    zt = zshell(lg["cy"]) - 1.0
    body = [(lg["cx"] - lg["w"] / 2, lg["cy"] - lg["h"] / 2), (lg["cx"] + lg["w"] / 2, lg["cy"] - lg["h"] / 2),
            (lg["cx"] + lg["w"] / 2, lg["cy"] + lg["h"] / 2), (lg["cx"] - lg["w"] / 2, lg["cy"] + lg["h"] / 2)]
    roof = [(lg["cx"] - lg["w"] / 2 - 1, lg["cy"] + lg["h"] / 2), (lg["cx"] + lg["w"] / 2 + 1, lg["cy"] + lg["h"] / 2),
            (lg["cx"], lg["cy"] + lg["h"] / 2 + lg["roof"])]
    plate = diff(plate, [union([extrude_pts(body, zt - lg["depth"], zt + 0.5),
                                extrude_pts(roof, zt - lg["depth"], zt + 0.5)])])
    plate = union([plate] + [mcyl(x, y, p["cav_top"] - 6, p["cav_top"] + 0.5, p["post_d"] / 2) for x, y in POSTS])
    plate = diff(plate, [mcyl(x, y, p["cav_top"] - 7, p["cav_top"] + 1, p["hole_m3"] / 2) for x, y in POSTS])
    if p["gpio_slot"]:
        plate = diff(plate, [mbox(100.0, 61.0, p["cav_top"] - 1, 150.0, 67.0, zshell(101) + 1)])
    return plate


def build_diffuseur():
    b0, b1 = P["led_band"]
    strips = [sloped_box(4, OX - 4, 0.8, 2.2, lambda y: zshell(y) + b0, lambda y: zshell(y) + b1),
              sloped_box(0.8, 2.2, 4, OY - 4, lambda y: zshell(y) + b0, lambda y: zshell(y) + b1),
              sloped_box(4, OX - 4, OY - 2.2, OY - 0.8, lambda y: zshell(y) + b0, lambda y: zshell(y) + b1)]
    return union(strips)


def ghosts():
    v = P["voice"]
    vx, vy = P["voice_xy"]
    return [
        mbox(BX, BY, PCB_BOT, BX + 85, BY + 56, PCB_TOP),
        mbox(BX + 20, BY + 8, PCB_TOP, BX + 70, BY + 48, PCB_TOP + 13.7),
        sloped_box(vx, vx + v["w"], vy, vy + v["w"], lambda y: zshell(y) - v["h"] - 1.0,
                   lambda y: zshell(y) - 1.0),
    ]


def main():
    os.makedirs(P["outdir"], exist_ok=True)
    base, plate, diffu = build_base(), build_plate(), build_diffuseur()
    for name, m in [("base", base), ("plateau", plate), ("diffuseur", diffu)]:
        m.export(os.path.join(P["outdir"], f"{name}.stl"))
        print(f"{name}: watertight={m.is_watertight} volume={m.volume:.0f} mm3 "
              f"bbox={m.bounds[0].round(1)}..{m.bounds[1].round(1)}")
    asm = union([base, plate, diffu] + ghosts())
    asm.export(os.path.join(P["outdir"], "apercu.stl"))
    solid = union([base, plate, diffu])
    for nm, g in [("cooler", ghosts()[1]), ("voice", ghosts()[2]), ("pcb", ghosts()[0])]:
        inter = trimesh.boolean.intersection([solid, g], engine="manifold")
        print(f"interference {nm}: {inter.volume:.1f} mm3 (doit etre ~0)")
    print("OK ->", P["outdir"])


if __name__ == "__main__":
    main()
