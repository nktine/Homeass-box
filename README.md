# Boîtier hub Home Assistant pour imprimante 3D (Raspberry Pi 5 + Voice PE)

Boîtier monobloc "premium" en 2 pièces imprimables (base + couvercle), conçu pour
remplacer l'actuelle coque du Pi 5 et accueillir en plus le **Home Assistant Voice
Preview Edition** de Nabu Casa. Il se fixe sur le cadre de l'imprimante (profil
aluminium 2020 ou 2040) ou au mur.

```
        189 mm
  +----------------------+------------------+
  |  BAIE VOICE (ouverte)|   BAIE PI 5      |
  |  84x84x21 + grilles   |   carte +         |  94 mm
  |  HP 3 côtés, ergots   |   Active Cooler   |
  |  notch USB-C cloison  |   + couvercle     |
  |                      |   honeycomb       |
  +----------------------+------------------+
   avant : USB-C + 2x micro-HDMI (Pi) | mur droit : 4x USB-A + RJ45
   arrière : rail 2020/2040 + M5, sortie câbles, entrées d'air
```

Dimensions extérieures : **189 x 94 x 32,5 mm** (hors rail arrière : +6,5 mm).

## Contenu

| Élément | Détail |
|---|---|
| Raspberry Pi 5 | nu, sur 4 entretoises M2.5 (pattern 58 x 49 mm), trous Ø2,7 |
| Active Cooler | 13,7 mm au-dessus du PCB — **4,7 mm de marge** sous le couvercle |
| Home Assistant Voice PE | 84 x 84 x 21 mm, baie ouverte dessus (micros/LED/dial dégagés), 4 ergots de maintien, grilles HP alignées sur les 3 côtés enceintes |
| Câblage | canal à câbles dédié derrière la carte (passages de colliers), sortie arrière, le câble USB-C de la Voice passe par une encoche dans la cloison |
| Refroidissement | honeycomb (126 hexagones, 5 mm) dans le couvercle au-dessus du ventilo, fentes au fond + entrées d'air à l'arrière |
| Fixation | rail arrière pour profilé 2020 (`extrusion=20`) ou 2040 (`extrusion=40`) + 2 écrous en T M5 ; 2 trous de serrure pour montage mural |

## Génération des STL

```bash
pip install trimesh manifold3d shapely        # (+ matplotlib pour les aperçus)
python3 boitier_pi5_voice.py                  # -> out/base.stl, out/couvercle.stl, out/apercu.stl
python3 render.py                              # -> preview/*.png
```

Tout est paramétrable en haut du fichier (`P = dict(...)`) : `extrusion` (20/40),
`play` (jeu des ports), `vent` (zone honeycomb), `gpio_slot` (fente GPIO dans le
couvercle, off par défaut), `h_int` (hauteur interne), etc.

Cotes utilisées (modèle de référence officiel Pi 5 RP-004882-DD, z=0 = dessus PCB) :
USB x4 (bord x=85) y 22,30..54,66 / z -3,50..16,78 ; Ethernet y 2,25..18,15 / z -2,05..13,70 ;
USB-C (y=0) x 6,73..15,67 ; micro-HDMI x 22,55..29,05 et 35,95..42,45 ; microSD bord x=0.

## Impression (FDM)

- **PETG** recommandé (proximité imprimante, chaleur) ; PLA acceptable si Active Cooler actif.
- 0,20 mm (0,12 mm pour le couvercle si le honeycomb bouche), buse 0,4 mm.
- 3 périmètres, 20-25 % de remplissage, 4 couches pleines dessus/dessous.
- **Aucun support nécessaire** : base à plat (fond abajo), couvercle à plat.
- Brim 5 mm sur la base ; compensation "pied d'éléphant" 0,1-0,2 mm.
- Couvercle imprimé à l'envers (face lisse contre le plateau).
- Poids ~55-70 g de filament au total, ~2-3 h d'impression.

## Quincaillerie

| Qté | Pièce |
|---|---|
| 4 | vis M2.5 x 8 mm (carte sur entretoises, trous Ø2,2 auto-taraudeurs) |
| 4 | inserts laiton M3 x 4 mm à chaud (couvercle) + 4 vis M3 x 10 mm |
| 2 | écrous en T M5 + 2 vis M5 x 16 mm (fixation profilé) |
| 1 | alim USB-C PD 5 V/5 A (27 W) pour le Pi 5 |
| 1 | câble USB-C pour la Voice PE (alim séparée ou hub USB-C PD) |

## Montage

1. Visser le Pi 5 sur les 4 entretoises (Active Cooler déjà clipsé, ventilateur branché sur le connecteur FAN).
2. Insérer les 4 inserts M3 dans les bosses, poser le couvercle, visser.
3. Glisser la Voice PE dans sa baie (son port USB-C face à la cloison), son câble traverse l'encoche de la cloison puis le canal et sort à l'arrière.
4. Fixer au cadre de l'imprimante : glisser le rail arrière dans la fente du profilé 2020/2040, serrer les 2 M5. Ports USB/Ethernet dégagés sur le côté droit.

## Notes

- Le bouton power du Pi 5 n'est pas déporté : ouvrir le couvercle, ou utiliser un shutdown GPIO/soft.
- `gpio_slot=True` ajoute une fente dans le couvercle au-dessus du header GPIO 40 broches.
- Pour un HAT M.2 ou plus haut : augmenter `h_int` (ex. +8 mm pour un M.2 HAT+ sur entretoises 16 mm).
- Vérifier les températures en charge après montage (`vcgencmd measure_temp`) — le plastique isole, d'où les ventilations dimensionnées.
