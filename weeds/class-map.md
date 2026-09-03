# YOLO class map (v1)

Locked to `PROJECT.md`. Do not add classes unless that file changes. Detector trains in Grok Build (WSL, RTX 4090), not here.

## Names (`weeds.yaml`)

| id | name | What it is | What it is not |
|---:|---|---|---|
| 0 | `dandelion` | *Taraxacum* in turf: basal rosette, toothed leaves, yellow bloom, white seed head | Cat’s-ear / hawkweed if you cannot tell — leave unlabeled. Not crabgrass. |
| 1 | `clover` | *Trifolium* in turf: trifoliate leaves, white or red bloom | Wood sorrel / *Oxalis*. Not “any small white flower.” |
| 2 | `thistle` | *Cirsium* / *Carduus* in turf: spiny rosette or upright plant, purple/pink bloom | Mulch, pine cones, dried oak leaves. Not bull vs Canada as extra classes. |
| 3 | `mallow` | Common mallow (*Malva*) and ground ivy (*Glechoma*) as **one** spray class: round palmate / kidney leaves | Spotted spurge (fine ferny mats). Not clover. |

`nc: 4`. Never renumber 0/1/2. Id 3 is operator-added mallow.

## Background (not a class)

Turf grass, bare dirt, fence, tree, sky, hose, toys, shoes. Crabgrass, nutsedge, plantain, chickweed, spotted spurge, “other_weed.” Anything the operator would not confirm as a spray target.

Do **not** add `background`, `grass`, or `other`. Those pixels are unlabeled.

## Labeling rules

- One box per plant. Touching rosettes get two boxes. Do not draw a lawn-sized clover rectangle unless it is one plant.
- Box the whole visible plant (leaves + bloom + seed head). Do not box only the flower when the rosette is in frame.
- Skip boxes smaller than ~20 px on the short side (train 640–1280). Skip unreadable blur, motion smear, and plants cut so species is a guess.
- Skip satellite tiles, microscope, herbarium sheets, clip-art, and single-petal close-ups.
- Clover leaves without bloom are still class 1. Dandelion clocks are still class 0.
- A Bot or model opinion is labeling help, not a spray confirm.

## Split

Split by image/source, never by cropping one photo into train and val. Hold operator backyard photos (`weeds/inbox/`) as domain val. Stratify so thistle appears in val. Bloom-only sources must not hide in train.
