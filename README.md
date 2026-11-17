# Homeass-box — Boîtier hub Home Assistant pour imprimante 3D (Pi 5 + Voice PE)

Boîtier monobloc **style premium** (v2) en 3 pièces imprimables : base + couvercle deux tons
+ diffuseur de bandeau LED. Il remplace la coque actuelle du Pi 5 et intègre le
**Home Assistant Voice Preview Edition** de Nabu Casa. Fixation sur le cadre de
l'imprimante (profilé 2020/2040) ou au mur.

```
        189 mm
  +----------------------+------------------+
  |  BAIE VOICE (ouverte)|   BAIE PI 5      |
  |  micro-perforations   |   carte +         |  94 mm
  |  facon tissu, logo    |   Active Cooler   |
  |  grave, bandeau LED   |   + couvercle     |
  |  en base de facade    |   honeycomb fin   |
  +----------------------+------------------+
   avant : bandeau LED + USB-C + 2x micro-HDMI | droit : 4x USB-A + RJ45
   arriere : rail 2020/2040 + M5, sortie câbles, entrées d'air | dessous : 4 vis M3 + 4 pieds
```

Dimensions extérieures : **189 × 94 × 32,5 mm** (hors rail : +6,5 mm).

## Style (v2)

- Coins très arrondis (R16) + chanfrein du rebord supérieur → silhouette organique.
- Couvercle **deux tons** (ex. base gris clair / couvercle noir) posé avec un **jeu d'ombre** de 0,8 mm.
- **Vis cachées** : 4 vis M3 insérées par le **dessous** dans des plots du couvercle (inserts laiton M3).
- **Bandeau LED** en base de la façade (fente 40 × 3,5 mm) : ruban WS2812B collé au fond derrière la fente + diffuseur `lightbar.stl` imprimé en filament **translucide** et collé dans la fente.
- **Logo maison gravé** (0,7 mm) sur la façade au-dessus de la baie Voice.
- Grilles haut-parleur en **micro-perforations Ø1,8 mm** (pas 3,2 mm) sur les 3 côtés de la baie Voice — rendu "tissu".
- Honeycomb fin du couvercle : hexagones de 4 mm (126 → ~230 cellules).
- 4 **empreintes pour pieds caoutchouc** Ø12 × 1,5 mm sous le fond.

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
python3 boitier_pi5_voice.py                  # -> out/base.stl, couvercle.stl, lightbar.stl, apercu.stl
python3 render.py                              # -> preview/*.png
```

Paramètres en haut du fichier (`P = dict(...)`) : `extrusion`, `play` (jeu des ports),
`vent`, `spk_*` (perforations), `lightbar`, `logo_*`, `gpio_slot`, `h_int`, etc.

## Impression (FDM)

- **PETG** (proximité imprimante) ; PLA OK si Active Cooler actif. Buse 0,4 mm.
- 0,20 mm (0,12 mm pour le couvercle et le lightbar), 3 périmètres, 20–25 % infill, 4 couches pleines.
- **Aucun support** : base à plat, couvercle imprimé à l'envers (plots vers le haut), lightbar à plat.
- Brim 5 mm sur la base, compensation pied d'éléphant 0,1–0,2 mm.
- Couleurs : base gris clair/blanc, couvercle noir (ou l'inverse), lightbar translucide.
- ~60–75 g de filament au total, ~2,5–3 h.

## Quincaillerie

| Qté | Pièce |
|---|---|
| 4 | vis M2.5 × 8 (carte sur entretoises) |
| 4 | inserts laiton M3 × 4 (dans les plots du couvercle) + 4 vis M3 × 10 (par le dessous) |
| 2 | écrous en T M5 + vis M5 × 16 (profilé) |
| 4 | pieds caoutchouc Ø12 × 2 mm (stick-on) |
| 1 | alim USB-C PD 5 V/5 A (27 W) pour le Pi 5 |
| 1 | ruban LED WS2812B ~50 mm (5 V/GND/data sur GPIO18 du Pi) + câble USB-C pour la Voice |

## Montage

1. Pi 5 vissé sur les 4 entretoises (Active Cooler clipsé, FAN branché).
2. Voice PE dans sa baie (USB-C face à la cloison), son câble traverse la cloison → canal → sortie arrière.
3. Ruban LED collé au fond contre la façade avant, derrière la fente ; diffuseur collé dans la fente.
4. Couvercle posé, retourné, 4 vis M3 par le dessous. Pieds collés.
5. Rail arrière dans le profilé 2020/2040, serrage des 2 M5. Ports USB/Ethernet dégagés sur le côté droit.

## Notes

- Bouton power du Pi 5 non déporté (ouvrir le couvercle ou shutdown GPIO).
- `gpio_slot=True` ajoute une fente GPIO dans le couvercle.
- HAT M.2 ou plus haut : augmenter `h_int`.
- Vérifier `vcgencmd measure_temp` en charge après montage.
