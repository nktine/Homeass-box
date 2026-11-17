#!/usr/bin/env python3
"""Boitier premium monobloc pour hub Home Assistant sur imprimante 3D.

Contenu : Raspberry Pi 5 nu + Active Cooler (ventilateur 30 mm) + Home Assistant
Voice Preview Edition (84 x 84 x 21 mm) en baie ouverte.
Fixation : rail arriere pour profil aluminium 2020 ou 2040 (ecrous en T + M5).

Cotes Pi 5 issues du modele de reference officiel RP-004882-DD (z=0 = dessus PCB) :
  USB x4 (edge x=85)   : y 22.30..54.66, z -3.50..16.78
  Ethernet (x=85)      : y 2.25..18.15,  z -2.05..13.70
  USB-C (y=0)          : x 6.73..15.67,  z -0.80..3.16
  micro-HDMI 0 (y=0)   : x 22.55..29.05, z -0.55..2.97
  micro-HDMI 1 (y=0)   : x 35.95..42.45, z -0.55..2.97
  microSD (x=0, dessous): y 22.00..33.95, z -3.05..-1.60
  Trous M2.5 : rectangle 58 x 49 mm, a 3.5 mm des bords courts.
  Active Cooler : 13.7 mm au-dessus du dessus du PCB.

Usage : pip install trimesh manifold3d shapely matplotlib
         python3 boitier_pi5_voice.py
Genere : out/base.stl, out/couvercle.stl, out/apercu.stl
"""

import math
import os

import numpy as np
import trimesh
from shapely.geometry import Point, box
from shapely.affinity import rotate as shp_rotate

# ---------------------------------------------------------------- parametres
P = dict(
    wall=3.0,            # epaisseur des murs
    floor=3.0,           # epaisseur du fond
    lid_t=3.5,           # epaisseur du couvercle
    r_out=5.0,           # rayon des coins exterieurs
    h_int=26.0,          # hauteur interieur (dessus fond -> dessous couvercle)
    # baie Pi (interieur)
    px0=94.0, px1=186.0, py0=3.0, py1=91.0,
    # baie Voice (interieur) : x 3..91, y 3..91
    vx0=3.0, vx1=91.0, vy0=3.0, vy1=91.0,
    # carte Pi 5 : origine du repere carte (coin x=0,y=0) en coord. boitier
    bx=97.0, by=7.0,
    standoff_h=6.0,      # hauteur des entretoises (z au-dessus du fond)
    standoff_d=6.0, hole_m25=2.2,
    boss_d=8.0, hole_m3_insert=4.0,   # inserts laiton M3 pour le couvercle
    lid_screw_d=3.3,
    play=0.5,            # jeu autour des ouvertures de ports
    # ventilateur : clearance au-dessus du PCB (Active Cooler = 13.7, USB = 16.78)
    cooler_clear=18.0,
    # profil alu : 20 -> fente 6 mm, 40 -> fente 8 mm
    extrusion=20,
    rail_len=(100.0, 185.0), rail_protrude=6.5,
    bolt_x=(115.0, 170.0), bolt_d=5.5,
    # grille haut-parleur de la Voice (3 cotes)
    spk_len=56.0, spk_z=(8.0, 21.0), spk_slat=1.8, spk_gap=1.0,
    # honeycomb du couvercle
    hex_af=5.0, hex_dx=6.8, hex_dy=5.8,
    vent=(104.0, 176.0, 13.0, 81.0),   # x0,x1,y0,y1
    gpio_slot=False,
    outdir="out",
)

OUT_X = 189.0
OUT_Y = 94.0
BASE_H = P["floor"] + P["h_int"]          # 29 : dessus des murs de la base
LID_Z0 = BASE_H
OUT_Z = BASE_H + P["lid_t"]

BX, BY = P["bx"], P["by"]
PCB_BOT = P["floor"] + P["standoff_h"]     # z du dessous du PCB = 9
PCB_TOP = PCB_BOT + 1.6                    # 10.6


def zc(z_board):
    """Convertit un z relatif au dessus du PCB en z boitier."""
    return PCB_TOP + z_board


# ---------------------------------------------------------------- primitives
def rounded_rect(x0, y0, x1, y1, r):
    return box(x0, y0, x1, y1).buffer(r).buffer(-r)


def extrude(poly, z0, z1):
    return trimesh.creation.extrude_polygon(poly, z1 - z0).apply_translation([0, 0, z0])


def mbox(x0, y0, z0, x1, y1, z1):
    return trimesh.creation.box(bounds=[[x0, y0, z0], [x1, y1, z1]])


def mcyl(x, y, z0, z1, r, sections=48):
    m = trimesh.creation.cylinder(radius=r, height=z1 - z0, sections=sections)
    m.apply_translation([x, y, (z0 + z1) / 2])
    return m


def hex_prism(x, y, z0, z1, af):
    from shapely.geometry import Polygon
    r = af / math.sqrt(3.0)
    pts = [(x + r * math.cos(math.radians(60 * i)),
            y + r * math.sin(math.radians(60 * i))) for i in range(6)]
    return extrude(Polygon(pts), z0, z1)


def union(meshes):
    return trimesh.boolean.union(meshes, engine="manifold")


def diff(a, meshes):
    return trimesh.boolean.difference([a] + list(meshes), engine="manifold")


def cut_wall_x(solid, x0, x1, y0, y1, z0, z1):
    return diff(solid, [mbox(x0 - 1, y0, z0, x1 + 1, y1, z1)])


def cut_wall_y(solid, y0, y1, x0, x1, z0, z1):
    return diff(solid, [mbox(x0, y0 - 1, z0, x1, y1 + 1, z1)])


# ---------------------------------------------------------------- base
def build_base():
    p = P
    base = extrude(rounded_rect(0, 0, OUT_X, OUT_Y, p["r_out"]), 0, BASE_H)
    # cavites des deux baies
    base = diff(base, [
        mbox(p["vx0"], p["vy0"], p["floor"], p["vx1"], p["vy1"], BASE_H + 1),
        mbox(p["px0"], p["py0"], p["floor"], p["px1"], p["py1"], BASE_H + 1),
    ])
    # entretoises Pi (M2.5)
    holes = (p["bx"] + 13.5, p["bx"] + 71.5)
    vows = (p["by"] + 3.5, p["by"] + 52.5)
    posts = [mcyl(x, y, p["floor"], p["floor"] + p["standoff_h"], p["standoff_d"] / 2)
             for x in holes for y in vows]
    base = union([base] + posts)
    base = diff(base, [mcyl(x, y, p["floor"] - 1, p["floor"] + p["standoff_h"] + 1, p["hole_m25"] / 2)
                       for x in holes for y in vows])
    # bosses de couvercle (inserts M3)
    boss_xy = [(98, 7), (182, 7), (98, 87), (182, 87)]
    base = union([base] + [mcyl(x, y, p["floor"], BASE_H, p["boss_d"] / 2) for x, y in boss_xy])
    base = diff(base, [mcyl(x, y, p["floor"] - 1, BASE_H + 1, p["hole_m3_insert"] / 2) for x, y in boss_xy])
    # 4 ergots de maintien de la Voice (appuient sur le dessus de l'appareil, z=24..29)
    lip_top = P["floor"] + 21.0   # dessus de la Voice = 24
    for cx, cy in [(p["vx0"], p["vy0"]), (p["vx1"] - 12, p["vy0"]),
                   (p["vx0"], p["vy1"] - 12), (p["vx1"] - 12, p["vy1"] - 12)]:
        base = union([base, mbox(cx, cy, lip_top, cx + 12, cy + 12, BASE_H)])

    # ---- ouvertures ports carte (mur droit x=186..189 : USB + Ethernet)
    eth_y = (BY + 2.25, BY + 18.15)
    usb_y = (BY + 22.30, BY + 54.66)
    eth_cut = (eth_y[0] - p["play"], eth_y[1] + p["play"])
    usb_cut = (usb_y[0] - p["play"], usb_y[1] + p["play"])
    base = cut_wall_x(base, p["px1"], OUT_X, eth_cut[0], eth_cut[1], zc(-2.05) - p["play"], zc(13.70) + p["play"])
    base = cut_wall_x(base, p["px1"], OUT_X, usb_cut[0], usb_cut[1], zc(-3.50) - p["play"], zc(16.78) + p["play"])

    # ---- mur avant y=0..3 : USB-C + 2 micro-HDMI
    usbc_x = (BX + 6.73, BX + 15.67)
    hd0_x = (BX + 22.55, BX + 29.05)
    hd1_x = (BX + 35.95, BX + 42.45)
    base = cut_wall_y(base, 0, p["py0"], usbc_x[0] - p["play"], usbc_x[1] + p["play"], zc(-0.80) - p["play"], zc(3.16) + p["play"])
    for hx in (hd0_x, hd1_x):
        base = cut_wall_y(base, 0, p["py0"], hx[0] - p["play"], hx[1] + p["play"], zc(-0.55) - p["play"], zc(2.97) + p["play"])

    # ---- cloison x=91..94 : relief cote x=0 de la carte (PCIe/MIPI/microSD) + USB-C Voice
    base = cut_wall_x(base, p["vx1"], p["px0"], 4.0, 45.0, zc(-3.5) - 0.5, zc(3.5) + 1.0)
    base = cut_wall_x(base, p["vx1"], p["px0"], 50.0, 66.0, p["floor"], p["floor"] + 8.0)    # USB-C Voice

    # ---- mur arriere y=91..94 : sortie cables + entrees d'air
    base = cut_wall_y(base, p["py1"], OUT_Y, 135.0, 160.0, 5.0, 13.0)
    for x0, x1 in [(100.0, 130.0), (165.0, 180.0)]:
        z = 5.0
        while z + 2.2 <= 14.0:
            base = cut_wall_y(base, p["py1"], OUT_Y, x0, x1, z, z + 2.2)
            z += 3.4

    # ---- grilles haut-parleur Voice : avant, gauche, arriere
    zs = []
    z = p["spk_z"][0]
    while z + p["spk_slat"] <= p["spk_z"][1]:
        zs.append((z, z + p["spk_slat"]))
        z += p["spk_slat"] + p["spk_gap"]
    c = (p["vx0"] + p["vx1"]) / 2
    half = p["spk_len"] / 2
    for z0, z1 in zs:
        base = cut_wall_y(base, 0, p["wall"], c - half, c + half, z0, z1)          # avant
        base = cut_wall_x(base, 0, p["wall"], c - half, c + half, z0, z1)          # gauche
        base = cut_wall_y(base, p["vy1"], OUT_Y, c - half, c + half, z0, z1)       # arriere

    # ---- fentes de ventilation du fond (sous la carte)
    for x0 in (118.0, 128.0, 138.0, 148.0, 158.0):
        base = diff(base, [mbox(x0, 14.0, -1, x0 + 4.0, 56.0, p["floor"] + 1)])
    # ---- passages de colliers dans le canal a cables
    for x0 in (125.0, 150.0):
        base = diff(base, [mbox(x0, 68.0, -1, x0 + 5.0, 86.0, p["floor"] + 1)])

    # ---- rail de fixation profil alu (face arriere)
    slot_w = 5.6 if p["extrusion"] == 20 else 7.6
    rz0, rz1 = 16.4 - slot_w / 2, 16.4 + slot_w / 2
    rail = mbox(p["rail_len"][0], OUT_Y, rz0, p["rail_len"][1], OUT_Y + p["rail_protrude"], rz1)
    base = union([base, rail])
    for bx_ in p["bolt_x"]:
        hole = trimesh.creation.cylinder(radius=p["bolt_d"] / 2, height=p["rail_protrude"] + p["wall"] + 2, sections=32)
        hole.apply_transform(trimesh.transformations.rotation_matrix(math.pi / 2, [1, 0, 0]))
        hole.apply_translation([bx_, OUT_Y + p["rail_protrude"] / 2, 16.4])
        base = diff(base, [hole])
        kc = trimesh.creation.cylinder(radius=3.5, height=p["wall"] + 2, sections=32)
        kc.apply_transform(trimesh.transformations.rotation_matrix(math.pi / 2, [1, 0, 0]))
        kc.apply_translation([bx_, OUT_Y - p["wall"] / 2 + 0.5, 24.0])
        ks = mbox(bx_ - 1.75, OUT_Y - p["wall"] - 1, 18.0, bx_ + 1.75, OUT_Y + 1, 24.0)
        base = diff(base, [kc, ks])
    return base


# ---------------------------------------------------------------- couvercle
def build_lid():
    p = P
    lid = extrude(rounded_rect(p["vx1"], 0, OUT_X, OUT_Y, p["r_out"]), LID_Z0, OUT_Z)
    # honeycomb au-dessus de la carte
    af, dx, dy = p["hex_af"], p["hex_dx"], p["hex_dy"]
    x0, x1, y0, y1 = p["vent"]
    hexes = []
    row = 0
    y = y0 + dy / 2
    while y <= y1:
        off = (dx / 2) if (row % 2) else 0.0
        x = x0 + off + dx / 2
        while x <= x1:
            hexes.append(hex_prism(x, y, LID_Z0 - 1, OUT_Z + 1, af))
            x += dx
        y += dy
        row += 1
    lid = diff(lid, hexes)
    # trous de vis M3
    for x, y in [(98, 7), (182, 7), (98, 87), (182, 87)]:
        lid = diff(lid, [mcyl(x, y, LID_Z0 - 1, OUT_Z + 1, p["lid_screw_d"] / 2)])
    # fente GPIO optionnelle
    if p["gpio_slot"]:
        lid = diff(lid, [mbox(BX + 3.5 - 1, 61.0, LID_Z0 - 1, BX + 3.5 + 52, 67.0, OUT_Z + 1)])
    return lid


# ---------------------------------------------------------------- fantomes (verif)
def ghosts():
    g = []
    g.append(mbox(BX, BY, PCB_BOT, BX + 85, BY + 56, PCB_TOP))                    # PCB
    g.append(mbox(BX + 20, BY + 8, PCB_TOP, BX + 70, BY + 48, PCB_TOP + 13.7))    # Active Cooler
    g.append(mbox(5, 5, P["floor"], 89, 89, P["floor"] + 21))                     # Voice PE
    return g


def main():
    os.makedirs(P["outdir"], exist_ok=True)
    base = build_base()
    lid = build_lid()
    base.export(os.path.join(P["outdir"], "base.stl"))
    lid.export(os.path.join(P["outdir"], "couvercle.stl"))
    asm = union([base, lid] + ghosts())
    asm.export(os.path.join(P["outdir"], "apercu.stl"))
    for name, m in [("base", base), ("couvercle", lid)]:
        print(f"{name}: watertight={m.is_watertight} volume={m.volume:.0f} mm3 "
              f"bbox={m.bounds[0].round(1)}..{m.bounds[1].round(1)}")
    # controle d'interference fantomes vs boitier (PCB seul, hors trous de vis)
    solid = union([base, lid])
    cooler = ghosts()[1]
    voice = ghosts()[2]
    for nm, g in [("cooler", cooler), ("voice", voice)]:
        inter = trimesh.boolean.intersection([solid, g], engine="manifold")
        print(f"interference {nm}: {inter.volume:.1f} mm3 (doit etre ~0)")
    print("OK ->", P["outdir"])


if __name__ == "__main__":
    main()
