# Homeass-box — Boîtier hub Home Assistant pour imprimante 3D (Pi 5 + Voice PE)

Boîtier **v3.1 « tour premium »** en 3 pièces imprimables (base blanche + plateau noir
+ diffuseur d'anneau LED), dans le langage de design de la **Home Assistant Voice PE**
de votre visuel : rectangle arrondi **116 × 100 mm (coins R22)**, bi-ton blanc/noir,
**anneau LED périphérique à la base**, **logo maison gravé** en façade, parois
chanfreinées, vis cachées par le dessous, 4 pieds caoutchouc encastrés.

```
   dessus : plateau noir à couronne perforée (effet tissu) + Voice PE (84x84x21)
            posée dans son socle, dessus (micro/LED/bouton) dégagé
   base   : Pi 5 nu + Active Cooler, ports, anneau LED, logo
   arrière: rail 2020/2040 (2x écrou T M5) + sortie câbles + entrées d'air
   dessous: 4 vis M3 (plateau) + 4 pieds + fentes d'aération
```

Hauteur totale : **58 mm** (base 29 + plateau 3,5 + Voice 21 + ergots). Hors rail : +6,5 mm.

## Contenu / cotes

| Élément | Détail |
|---|---|
| Raspberry Pi 5 | nu, 4 entretoises M2.5 (pattern 58 × 49 mm, trous Ø2,7) |
| Active Cooler | 13,7 mm au-dessus du PCB → **4,7 mm de marge** sous le couvercle |
| Voice PE | 84 × 84 × 21 mm, baie ouverte (micros/LED/bouton dégagés), 4 ergots, câble USB-C via la cloison |
| Ports Pi 5 | cotes exactes du modèle de référence officiel RP-004882-DD (USB x4 + RJ45 à droite, USB-C + 2 micro-HDMI à l'avant, une seule ouverture pour les 4 USB) |
| Fixation | rail arrière profilé 2020 (`extrusion=20`) ou 2040 (`extrusion=40`), 2 écrous en T M5 ; trous de serrure muraux |
| Refroidissement | honeycomb au-dessus du ventilo, fentes au fond, entrées d'air à l'arrière, canal à câbles avec colliers |

## Génération

```bash
pip install trimesh manifold3d shapely        # + matplotlib pour les aperçus
python3 boitier_pi5_voice.py                  # -> out/base.stl, plateau.stl, diffuseur.stl, apercu.stl
python3 render.py                              # -> preview/*.png
```

Paramètres en haut du fichier (`P = dict(...)`) : `extrusion`, `play` (jeu des ports),
`vent`, `spk_*` (perforations), `lightbar`, `logo_*`, `gpio_slot`, `h_int`, etc.

## Impression (FDM)

- **PETG** (proximité imprimante) ; PLA OK si Active Cooler actif. Buse 0,4 mm.
- Couleurs : base **blanc/gris clair**, plateau **noir**, diffuseur **translucide**.
- 0,20 mm (0,12 mm pour le couvercle et le lightbar), 3 périmètres, 20–25 % infill, 4 couches pleines.
- **Aucun support** : base à plat, plateau imprimé à l'envers (plots et couronne vers le haut), diffuseur à plat.
- Brim 5 mm sur la base, compensation pied d'éléphant 0,1–0,2 mm.
- Couleurs : base gris clair/blanc, couvercle noir (ou l'inverse), lightbar translucide.
- ~60–75 g de filament au total, ~2,5–3 h.

## Quincaillerie

| Qté | Pièce |
|---|---|
| 4 | vis M2.5 × 8 (carte sur entretoises) |
| 4 | inserts laiton M3 × 4 (dans les plots du plateau) + 4 vis M3 × 10 (par le dessous) |
| 2 | écrous en T M5 + vis M5 × 16 (profilé) |
| 4 | pieds caoutchouc Ø12 × 2 mm (stick-on) |
| 1 | alim USB-C PD 5 V/5 A (27 W) pour le Pi 5 |
| 1 | ruban LED WS2812B ~400 mm faire le tour de la base (5 V/GND/data sur GPIO18 du Pi) + câble USB-C pour la Voice |

## Montage

1. Pi 5 vissé sur les 4 entretoises (Active Cooler clipsé, FAN branché).
2. Voice PE dans son socle sur le plateau (USB-C vers l'arrière), son câble traverse le plateau → canal → sortie arrière.
3. Ruban LED collé au fond tout autour de la base, derrière la fente périphérique ; anneau diffuseur collé dans la fente.
4. Plateau posé sur la base, retourné, 4 vis M3 par le dessous. Pieds collés.
5. Rail arrière dans le profilé 2020/2040, serrage des 2 M5. Ports USB/Ethernet dégagés sur le côté droit.

## Notes

- Bouton power du Pi 5 non déporté (ouvrir le couvercle ou shutdown GPIO).
- `gpio_slot=True` ajoute une fente GPIO dans le plateau.
- HAT M.2 ou plus haut : augmenter `h_int`.
- Vérifier `vcgencmd measure_temp` en charge après montage.
