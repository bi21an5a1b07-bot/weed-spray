"""YOLO class map. bot_files/weeds_class-map.md. Do not renumber 0/1/2.

Turf, dirt, crabgrass, plantain, and ``other_weed`` are unlabeled background, not a class.
"""

NAMES: dict[int, str] = {
    0: "dandelion",  # Taraxacum
    1: "clover",  # Trifolium, not Oxalis
    2: "thistle",  # Cirsium / Carduus as one class
    3: "mallow",  # Malva + Glechoma (ground ivy) as one spray target
}
NC = 4
"""Class count. Never renumber 0/1/2. Id 3 is operator-added mallow."""
CLASSES = frozenset(NAMES.values())
"""Allowed string labels for inject / confirm."""
NAME_TO_ID = {v: k for k, v in NAMES.items()}
"""Reverse map used by tests and future YOLO post-process."""
YAML_RELATIVE = "weeds/weeds.yaml"
"""Repo-relative Ultralytics data yaml; must list the same names."""
