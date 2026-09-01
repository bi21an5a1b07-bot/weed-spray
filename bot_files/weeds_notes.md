# Labeling rules (v1)

For boxes on `dandelion` (0), `clover` (1), `thistle` (2) only. Turf is unlabeled background. This is training hygiene, not a spray confirm.

## Box geometry

- **One box per plant.** If two rosettes touch, two boxes. Do not merge a patch of clover into one lawn-sized rectangle unless it is clearly one plant.
- Box the **whole visible plant** in that frame: leaves + bloom + seed head if they belong to the same plant. Do not box only the flower when the rosette is visible.
- If only a bloom is visible (leaves hidden in grass), box the bloom plus whatever plant tissue you can see. Tag the source in `sources.md` as bloom-heavy.
- Skip a plant if the box would be mostly other plants.

## Minimum box

- Skip boxes smaller than about **20 px** on the short side at the training resolution you will actually use (typical 640–1280). Below that the detector learns noise.
- Skip **unreadable blur**, motion smear, heavy compression blocks, and plants cut by the frame so that species is a guess.
- Skip extreme close-ups where a single petal fills the image (no plant context, wrong GSD for a quad).

## Class-specific

### dandelion

- Include: jagged basal rosette, yellow capitulum, white seed head (“clock”).
- Flower and seed head of the same plant: still class 0, one box if they are one plant; two boxes if they are two plants.
- Do not label cat’s-ear / hawkweed / false dandelion if you cannot tell. Leave unlabeled.
- Crabgrass clumps are **not** dandelion. Unlabeled.

### clover

- Include: trifoliate *Trifolium* leaves (often a pale chevron) and white or red flower heads.
- Bloom vs leaf: both are class 1. A patch with only leaves and no bloom is still clover.
- Wood sorrel / *Oxalis* (heart-shaped leaflets, often folded) is **not** clover. Unlabeled.
- Do not label “any small white flower in grass.”

### thistle

- Include: spiny rosette and upright *Cirsium* / *Carduus* (bull, Canada, musk, etc. as one class).
- Young rosettes in turf matter more for a 6–12 in hover than a tall roadside bloom. Prefer those if the source has them.
- Mulch chunks, pine cones, and dried oak leaves are common false positives. Do not label them.
- Do not split bull vs Canada into extra classes.

## Ignore (never a class)

- Turf grass, dirt, fence, trees, sky, hose, toys, shoes
- Crabgrass, nutsedge, plantain, chickweed, “other_weed”
- People, pets, garden beds (also out of mission; do not train on them as targets)

## Domain

- Prefer RGB lawn-level or 1–10 m nadir (quad-like). Tractor-boom and cotton-field sets are last-resort and must be marked domain-shift in `sources.md`.
- Operator backyard photos in `weeds/inbox/` are the domain val set. Label them with these rules; do not treat a model or a Bot opinion as a spray confirm.

## Failure modes to watch in val

- Crabgrass / other grassy weeds scored as dandelion
- Clover bloom vs clover leaf (model only fires on flowers)
- Thistle vs mulch / pine cone
- Yellow flowers that are not dandelion (cat’s-ear, hawkweed, buttercup)
- White puff seed heads vs trash / dandelion clocks

If a source is almost all flowers and no rosettes, do not hide that in train. Put some of it in val so the gap stays visible.
