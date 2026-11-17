#!/usr/bin/env python3
"""Homeass-box v3.1 "tour premium" - boitier hub Home Assistant facon appareil.

Rectangle arrondi 116 x 100 mm (coins R22, rebord chanfreine) : base blanche avec
anneau LED a la base + logo maison grave + ports, plateau superieur noir perce
(effet tissu) servant de socle a la Voice PE (84x84x21, dessus degage),
Pi 5 + Active Cooler en dessous. Fixation profile 2020/2040 a l'arriere,
vis du plateau par le dessous, 4 pieds encastres.

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
    ox=116.0, oy=100.0,                  # empreinte exterieure
    wall=3.0, floor=3.0, h_int=26.0, r_out=22.0, chamfer=1.0,
    base_h=29.0,
    plate_t=3.5, plate_off=1.5, plate_chamfer=1.2,
    bx=6.0, by=6.0, standoff_h=6.0, standoff_d=6.0, hole_m25=2.2,
    post_d=8.0, hole_m3=4.0, floor_screw_d=3.4,
    play=0.5,
    extrusion=20, rail=(25.0, 90.0), rail_protrude=6.5,
    bolt_x=(40.0, 76.0), bolt_d=5.5,
    led_z=(4.0, 6.2),
    vent_ring=6.0, hex_af=3.5, hex_dx=4.8, hex_dy=4.157,
    cradle=dict(rimx0=13.0, rimx1=107.0, rimy0=3.0, rimy1=97.0, rim_h=6.0, lip=12.0, lip_top=58.0),
    voice=dict(w=84.0, h=21.0),          # position: centre dans le pocket
    cable_hole=(55.0, 65.0, 92.0, 98.0),
    logo=dict(cx=58.0, z0=20.0, w=14.0, h=6.5, roof=2.8, depth=0.7),
    exhaust=(8.0, 92.0, 7.0, 27.0), hole_d=1.8, pitch=3.2,
    back_slats=((8.0, 38.0), (78.0, 108.0), 7.0, 15.0),
    cable_notch=(45.0, 75.0, 7.0, 14.0),
    gpio_slot=False,
    outdir="out",
)

OX, OY = P["ox"], P["oy"]
BASE_H = P["base_h"]
PLATE_Z0, PLATE_Z1 = BASE_H, BASE_H + P["plate_t"]
BX, BY = P["bx"], P["by"]
PCB_BOT = P["floor"] + P["standoff_h"]
PCB_TOP = PCB_BOT + 1.6
VOICE_TOP = PLATE_Z1 + P["voice"]["h"]
POSTS = ((6.5, 6.5), (OX - 6.5, 6.5), (6.5, OY - 6.5), (OX - 6.5, OY - 6.5))
C = P["cradle"]
POCKET = (C["rimx0"] + P["wall"], C["rimy0"] + P["wall"], C["rimx1"] - P["wall"], C["rimy1"] - P["wall"])
VOICE_XY = ((POCKET[0] + POCKET[2] - P["voice"]["w"]) / 2, (POCKET[1] + POCKET[3] - P["voice"]["w"]) / 2)


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
        faces += [[i, j, n + j], [i, n + j, n + i]]
    for i in range(1, n - 1):
        faces += [[0, i + 1, i], [n, n + i, n + i + 1]]
    m = trimesh.Trimesh(vertices=verts, faces=faces, process=True)
    m.fix_normals()
    return m


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
    r, ch = p["r_out"], p["chamfer"]
    base = extrude_pts(rounded_rect_pts(0, 0, OX, OY, r), 0, BASE_H - ch)
    base = union([base, loft(rounded_rect_pts(0, 0, OX, OY, r), BASE_H - ch,
                             rounded_rect_pts(ch, ch, OX - ch, OY - ch, r - ch), BASE_H)])
    base = diff(base, [mbox(p["wall"], p["wall"], p["floor"], OX - p["wall"], OY - p["wall"], BASE_H + 1)])
    standoffs = [(BX + 71.5, BY + 3.5), (BX + 13.5, BY + 3.5), (BX + 71.5, BY + 52.5), (BX + 13.5, BY + 52.5)]
    base = union([base] + [mcyl(x, y, p["floor"], p["floor"] + p["standoff_h"], p["standoff_d"] / 2)
                           for x, y in standoffs])
    base = diff(base, [mcyl(x, y, p["floor"] - 1, p["floor"] + p["standoff_h"] + 1, p["hole_m25"] / 2)
                       for x, y in standoffs])
    base = diff(base, [mcyl(x, y, -1, p["floor"] + 1, p["floor_screw_d"] / 2) for x, y in POSTS])
    for x0 in (30.0, 40.0, 50.0, 60.0, 70.0):
        base = diff(base, [mbox(x0, 20.0, -1, x0 + 4.0, 60.0, p["floor"] + 1)])
    for fx, fy in [(14, 14), (OX - 14, 14), (14, OY - 14), (OX - 14, OY - 14)]:
        base = diff(base, [mcyl(fx, fy, -1, 1.5, 6.0)])
    lz0, lz1 = p["led_z"]
    base = cut_wall_y(base, 0, p["wall"], 2, OX - 2, lz0, lz1)
    base = cut_wall_y(base, OY - p["wall"], OY, 2, OX - 2, lz0, lz1)
    base = cut_wall_x(base, 0, p["wall"], 2, OY - 2, lz0, lz1)
    base = cut_wall_x(base, OX - p["wall"], OX, 2, OY - 2, lz0, lz1)
    usbc = (BX + 85 - 15.67 - p["play"], BX + 85 - 6.73 + p["play"])
    base = cut_wall_y(base, 0, p["wall"], usbc[0], usbc[1], zc(-0.80) - p["play"], zc(3.16) + p["play"])
    for bx_ in (22.55, 35.95):
        hx = (BX + 85 - (bx_ + 3.25) - p["play"], BX + 85 - (bx_ - 3.25) + p["play"])
        base = cut_wall_y(base, 0, p["wall"], hx[0], hx[1], zc(-0.55) - p["play"], zc(2.97) + p["play"])
    eth = (BY + 2.25 - p["play"], BY + 18.15 + p["play"])
    usb = (BY + 22.30 - p["play"], BY + 54.66 + p["play"])
    base = cut_wall_x(base, OX - p["wall"], OX, eth[0], eth[1], zc(-2.05) - p["play"], zc(13.70) + p["play"])
    base = cut_wall_x(base, OX - p["wall"], OX, usb[0], usb[1], zc(-3.50) - p["play"], zc(16.78) + p["play"])
    lg = p["logo"]
    body = [(lg["cx"] - lg["w"] / 2, lg["z0"]), (lg["cx"] + lg["w"] / 2, lg["z0"]),
            (lg["cx"] + lg["w"] / 2, lg["z0"] + lg["h"]), (lg["cx"] - lg["w"] / 2, lg["z0"] + lg["h"])]
    roof = [(lg["cx"] - lg["w"] / 2 - 0.8, lg["z0"] + lg["h"]),
            (lg["cx"] + lg["w"] / 2 + 0.8, lg["z0"] + lg["h"]),
            (lg["cx"], lg["z0"] + lg["h"] + lg["roof"])]
    base = diff(base, [union([prism_xz(body, -0.1, lg["depth"]), prism_xz(roof, -0.1, lg["depth"])])])
    a0, a1, z0, z1 = p["exhaust"]
    d, pitch = p["hole_d"], p["pitch"]
    perfs = []
    a = a0 + d / 2
    while a <= a1 - d / 2:
        z = z0 + d / 2
        while z <= z1 - d / 2:
            perfs.append(cyl_x(-1.0, a, z, d / 2, p["wall"] + 2))
            z += pitch
        a += pitch
    base = diff(base, perfs)
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
        base = diff(base, [cyl_y(bx_, OY - p["wall"] - 1, 24.0, 3.5, p["wall"] + 2)])
        base = diff(base, [mbox(bx_ - 1.75, OY - p["wall"] - 1, 18.0, bx_ + 1.75, OY + 1, 24.0)])
    return base


def build_plate():
    p = P
    po, pc = p["plate_off"], p["plate_chamfer"]
    x0, y0, x1, y1 = po, po, OX - po, OY - po
    r = p["r_out"] - 2
    plate = loft(rounded_rect_pts(x0 + 0.6, y0 + 0.6, x1 - 0.6, y1 - 0.6, r - 0.6), PLATE_Z0,
                 rounded_rect_pts(x0, y0, x1, y1, r), PLATE_Z0 + 0.6)
    plate = union([plate, extrude_pts(rounded_rect_pts(x0, y0, x1, y1, r), PLATE_Z0 + 0.6, PLATE_Z1 - pc)])
    plate = union([plate, loft(rounded_rect_pts(x0, y0, x1, y1, r), PLATE_Z1 - pc,
                                rounded_rect_pts(x0 + pc, y0 + pc, x1 - pc, y1 - pc, r - pc), PLATE_Z1)])
    w = p["vent_ring"]
    af, dx, dy = p["hex_af"], p["hex_dx"], p["hex_dy"]
    ch = p["cable_hole"]
    hexes = []
    for rx0, ry0, rx1, ry1 in [(x0 + 0.5, y0 + 0.5, x0 + w, y1 - 0.5),
                               (x1 - w, y0 + 0.5, x1 - 0.5, y1 - 0.5),
                               (x0 + 0.5, y0 + 0.5, x1 - 0.5, y0 + w),
                               (x0 + 0.5, y1 - w, x1 - 0.5, y1 - 0.5)]:
        row = 0
        y = ry0 + dy / 2
        while y <= ry1:
            off = dx / 2 if row % 2 else 0.0
            x = rx0 + off + dx / 2
            while x <= rx1:
                if all((x - px) ** 2 + (y - py) ** 2 > 6.5 ** 2 for px, py in POSTS) \
                   and not (ch[0] - 2 < x < ch[1] + 2 and ch[2] - 2 < y < ch[3] + 2) \
                   and not (C["rimx0"] - 1 < x < C["rimx1"] + 1 and C["rimy0"] - 1 < y < C["rimy1"] + 1):
                    hexes.append(hex_prism(x, y, PLATE_Z0 - 1, PLATE_Z1 + 1, af))
                x += dx
            y += dy
            row += 1
    plate = diff(plate, hexes)
    plate = diff(plate, [mbox(ch[0], ch[2], PLATE_Z0 - 1, ch[1], ch[3], PLATE_Z1 + 1)])
    plate = union([plate] + [mcyl(x, y, PLATE_Z0 - 6, PLATE_Z0 + 0.5, p["post_d"] / 2) for x, y in POSTS])
    plate = diff(plate, [mcyl(x, y, PLATE_Z0 - 7, PLATE_Z0 + 1, p["hole_m3"] / 2) for x, y in POSTS])
    c = P["cradle"]
    w = p["wall"]
    rim = [mbox(c["rimx0"], c["rimy0"], PLATE_Z1, c["rimx1"], c["rimy0"] + w, PLATE_Z1 + c["rim_h"]),
           mbox(c["rimx0"], c["rimy1"] - w, PLATE_Z1, c["rimx1"], c["rimy1"], PLATE_Z1 + c["rim_h"]),
           mbox(c["rimx0"], c["rimy0"] + w, PLATE_Z1, c["rimx0"] + w, c["rimy1"] - w, PLATE_Z1 + c["rim_h"]),
           mbox(c["rimx1"] - w, c["rimy0"] + w, PLATE_Z1, c["rimx1"], c["rimy1"] - w, PLATE_Z1 + c["rim_h"])]
    plate = union([plate] + rim)
    for cx, cy in [(c["rimx0"], c["rimy0"]), (c["rimx1"] - c["lip"], c["rimy0"]),
                   (c["rimx0"], c["rimy1"] - c["lip"]), (c["rimx1"] - c["lip"], c["rimy1"] - c["lip"])]:
        plate = union([plate, mbox(cx, cy, VOICE_TOP, cx + c["lip"], cy + c["lip"], c["lip_top"])])
    if p["gpio_slot"]:
        plate = diff(plate, [mbox(BX + 2.5, 60.0, PLATE_Z0 - 1, BX + 55.5, 66.0, PLATE_Z1 + 1)])
    return plate


def build_diffuseur():
    z0, z1 = P["led_z"]
    ring = extrude_pts(rounded_rect_pts(1, 1, OX - 1, OY - 1, P["r_out"] - 1), z0, z1)
    return diff(ring, [extrude_pts(rounded_rect_pts(3, 3, OX - 3, OY - 3, P["r_out"] - 3), z0 - 1, z1 + 1)])


def ghosts():
    v = P["voice"]
    return [
        mbox(BX, BY, PCB_BOT, BX + 85, BY + 56, PCB_TOP),
        mbox(BX + 20, BY + 8, PCB_TOP, BX + 70, BY + 48, PCB_TOP + 13.7),
        mbox(VOICE_XY[0], VOICE_XY[1], PLATE_Z1, VOICE_XY[0] + v["w"], VOICE_XY[1] + v["w"], PLATE_Z1 + v["h"]),
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
