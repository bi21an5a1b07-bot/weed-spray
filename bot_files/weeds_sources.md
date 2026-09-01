# Public RGB sources (v1 survey)

Checked: 2026-08-30. No archives downloaded. Classes locked: `dandelion`=0, `clover`=1, `thistle`=2. Turf is background.

There is **no** public, license-clear, US-lawn, 3-class detection set. Everything below is a building block. Counts are observations or paper tables, not “ready YOLO boxes,” unless noted.

## Use (or near-use)

| Dataset | Official URL | License | dandelion | clover | thistle | View | Boxes? | Notes |
|---|---|---|---:|---:|---:|---|---|---|
| iNaturalist live API (research-grade + photos) | https://api.inaturalist.org/v1/observations — taxa 47602 / 55745+51875 / 60132+52989+76007 | Per-photo CC mix. Majority **CC-BY-NC**. Commercial-safe = **CC0 + CC-BY only**. Also iNat ToS | 164,687 obs (US 60,460). CC0 5,069 + CC-BY 13,647 | White 246,466 (US 115,900); red 232,540 (US 83,846). CC0+CC-BY minority | C. arvense 160,061 (US 46,941); C. vulgare 155,310 (US 57,281); C. nutans 40,751 (US 27,149) | Mixed citizen photos, bloom-heavy, not 1–10 m nadir | No | Obs ≠ images. Filter US + CC0/CC-BY, then box. Do not scrape against ToS |
| iNaturalist Open Data (AWS) | https://github.com/inaturalist/inaturalist-open-data — `s3://inaturalist-open-data` | Same per-photo CC | Same pool; per-class file count unpublished without metadata scan | same | same | same | No | Monthly metadata snapshot. **Do not pull the photo bucket until approved** |
| GBIF StillImage | https://api.gbif.org/v1/occurrence/search — taxonKeys 5394163 / 5358748+8324121 / 3113414+3112801+8185959 | Publisher mix. iNat slice is CC0 / CC-BY / CC-BY-NC | StillImage 203,274; human 190,240; US 50,970; CC_BY_4_0 18,953 | White 232,613 (US 91,849); red 243,960 (US 68,111) | C. arvense 196,047 (US 38,696); C. vulgare 192,677 (US 46,857); C. nutans 42,940 (US 21,478) | Mixed; herbarium unless `HUMAN_OBSERVATION` | No | Overlaps iNat. Filter specimens out |
| GrassClover | https://vision.eng.au.dk/grass-clover-dataset/ — paper DOI 10.1109/CVPRW.2019.00325 | **CC BY-SA** (page unversioned; Kaggle rehost says 4.0). ShareAlike | Paper Fig. 3: **16** dandelion cut-outs used to synthesize 8,000 images. Real 31,600 unlabeled may contain more — unpublished | **Primary class.** White+red clover in grass canopy. Fig. 3 cut-outs: white leaf 37, white flower 36, red leaf 23, red flower 1 | Fig. 3: **6** thistle cut-outs. Real “weeds” lumps several spp. | Nadir close-up, 4–8 px/mm (quad-low). Danish grass-clover leys | Segmentation, not YOLO boxes. 15 real images hand-labeled | Map white+red → `clover`. Keep ryegrass as background. Convert masks → boxes later |
| Broadleaf Weeds in Common Couch (Weed-AI) | https://weed-ai.sydney.edu.au/datasets/8b14a44b-bc7f-4b92-9bc0-224a2a2c4e22 | **Unclear** on official page. Do not assume CC | **75 images / 533 boxes** *T. officinale* | none | none (Sonchus / Erigeron present — do not map) | Waist-high top-down over couch grass, Perth WA | **Yes (WeedCOCO)** | Closest public turf-like detection set. WA, not US lawn. Resolve license before commercial use |
| CropAndWeed (WACV 2023) | https://github.com/cropandweed/cropandweed-dataset — paper WACV 2023 | **Custom non-commercial.** No image redistribution. Trained models OK if they cannot recover data | Suppl: *Taraxacum* **1 image / 1 instance** — not usable | none | *C. arvense* **410 images / 2,693 instances**. Do **not** use Fine24 “thistle” super-class without remapping | Field tractor / close nadir, European crops | Yes: boxes + masks | Thistle plant yes, lawn no. Research-only |
| OPPD | https://vision.eng.au.dk/open-plant-phenotyping-database/ — DOI 10.3390/rs12081246 | **CC BY-NC-SA 4.0** | none | none | *Cirsium arvense* (CIRAR) present. Per-class count unpublished (dataset 7,590 img / 315,038 objects / 47 spp.) | Semi-field seedlings, ~6.6 px/mm | Yes, boxes | Seedling thistle only. Full dump tens of GB — skip for now |
| Manitoba weed seedlings (Dryad) | https://doi.org/10.5061/dryad.gtht76hhz — paper 10.1371/journal.pone.0243923 | Dryad default **CC0** (confirm on record) | **4,797** *T. officinale* | none | **4,706** *C. arvense* | Lab robot, pots/soil, not turf. 34,666 RGB classif. | No (image-level) | **6.90 GB**. Good pretrain, large domain gap |
| Oxford 102 Flowers | https://www.robots.ox.ac.uk/~vgg/data/flowers/102/ | **No license on official page.** Treat as custom academic | **92** common dandelion | none | spear thistle **48**; globe thistle **45** (*Echinops* — **do not map** to `thistle`) | Bloom close-ups | Seg masks, not detection | Bloom-only, ~329 MB |
| Open Images V7 | https://storage.googleapis.com/openimages/web/index.html | Annotations CC BY 4.0. Images listed CC BY 2.0; **verify each image** | Image-level Dandelion `/m/0fr19`. Val human-verified: **24 pos**. **Not boxable** | Clover `/m/0c2pc`. Val **9 pos**. Not boxable | Thistle `/m/06tzj3`. Val **23 pos**. Not boxable | Flickr mixed | No boxes for these 3 | Train image-level CSV 1.53 GB not scanned. Full image dump hundreds of GB — skip |
| Yu et al. 2019 ryegrass/lawn | https://doi.org/10.3389/fpls.2019.01422 | Paper CC BY. **Images “available on request”** | Paper: 6,500 pos crops; DetectNet train **810** / val+test **100** each | not a class (do not add ground ivy / spurge from the paper) | none | **US golf/institutional lawns** (IN) + Saskatoon. 0.05 cm/px handheld, turf height. Closest to 6–12 in AGL | DetectNet boxes on 810+300 | **Best domain match, not a public dump.** Request if wanted |
| Kaggle “Multiple weed species detection” | https://www.kaggle.com/datasets/akhilesh19sharma/multiple-weed-species-detection | **CC0** | **227** (in a 2,349-image 5-spp augmented set) | none | none | Ag field, not lawn | Yes (COCO) | Provenance/augmentation weakly documented |
| iNat 2021 (FGVC8) | https://github.com/visipedia/inat_comp/blob/master/2021/README.md | **Non-commercial research only.** Do not redistribute images | Whether *T. officinale* is in the 10k classes: unpublished (train.json 221 MB not fetched) | unpublished | unpublished | Citizen mixed, 500 px max | No | Train images **224 GB** — skip |

Counts for iNat/GBIF are **observations with photos**, not files. CC0+CC-BY commercial-trainable pool (global, research+photos): dandelion ~18.7k obs, white clover ~26.6k, red clover ~26.0k, C. arvense ~22.2k, C. vulgare ~20.5k, musk thistle ~4.2k.

## Skip (verified no overlap or wrong domain)

| Dataset | URL | Why |
|---|---|---|
| DeepWeeds | https://doi.org/10.1038/s41598-018-38343-3 (CC BY 4.0) | AU rangeland 8 spp. None of the three classes |
| CottonWeedID15 | https://www.kaggle.com/datasets/yuzhenlu/cottonweedid15 (CC BY-NC 4.0) | Cotton weeds. **Crabgrass is a lookalike, not a class** |
| CottonWeedDet12 | https://doi.org/10.5281/zenodo.7535814 — license conflict CC-BY vs CC-BY-NC | No target classes. 28.6 GB |
| WeedNet / Sugar Beets 2016 | https://www.ipb.uni-bonn.de/data/sugarbeets2016/ | Crop vs weed, no species for our three |
| PlantVillage | https://github.com/spMohanty/PlantVillage-Dataset | Crop-disease leaves, gray bg |
| Open Sprayer (Kaggle) | https://www.kaggle.com/datasets/gavinarmstrong/open-sprayer-images (CC0) | Broad-leaved dock |
| CWFID / Plant Seedlings (Aarhus) | various | Binary crop/weed or other spp. |
| Roboflow Universe | per-project | Remixes. Use only if the project prints CC BY/CC0 **and** photos are original. Prefer primary sources |

## Gaps

- **Thistle at 6–12 in AGL over turf:** nothing public. Highest-priority collect.
- **Clover leaves vs blooms:** GrassClover has leaves; iNat is flower heads. Need trifoliate mats without flowers.
- **Dandelion clocks and mowed rosettes:** public data is yellow blooms. Yu 2019 (closed) mixed stages.
- **1–10 m US lawn nadir:** almost nothing. Operator flights will own this band.
- **3-class YOLO labels:** every public set needs remapping and/or new boxes.
- **Crabgrass:** keep in negatives. Yu 2019 false-positive’d *Digitaria* as dandelion. Do not add a 4th class.

## Later ingest (operator decides; 4090, not this computer)

1. Operator-captured US lawn RGB at 1–10 m and 6–12 in AGL.
2. Weed-AI Couch dandelion boxes — after license check.
3. GrassClover masks → boxes (SA).
4. iNat **CC0+CC-BY** research-grade, US geotag, then box.
5. CropAndWeed *C. arvense* instances only (NC research).
6. Manitoba Dryad classif. pretrain (6.9 GB).
7. Request Yu et al. 2019 from the corresponding author.

Do not mix CottonWeed crabgrass, *Sonchus*, *Erigeron*, *Echinops* globe thistle, or crimson clover into the three YOLO names.
