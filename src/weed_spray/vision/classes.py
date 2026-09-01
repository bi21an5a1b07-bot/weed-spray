"""Frozen v1 class map. bot_files/weeds_class-map.md. Do not renumber.

Turf, dirt, crabgrass, and ``other_weed`` are unlabeled background, not a class.
"""

NAMES: dict[int, str] = {
    0: "dandelion",  # Taraxacum
    1: "clover",  # Trifolium, not Oxalis
    2: "thistle",  # Cirsium / Carduus as one class
}
NC = 3
"""Locked class count. Never add a fourth YOLO class in v1."""
CLASSES = frozenset(NAMES.values())
"""The three allowed string labels for inject / confirm."""
NAME_TO_ID = {v: k for k, v in NAMES.items()}
"""Reverse map used by tests and future YOLO post-process."""
YAML_RELATIVE = "weeds/weeds.yaml"
"""Repo-relative Ultralytics data yaml; must list the same three names."""
