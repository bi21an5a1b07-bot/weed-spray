Save this as a skill named **weed-dataset-survey**. Enable it on the `weeds` Bot.

When to use: operator asks for training data, class names, labeling rules, or whether a photo is dandelion/clover/thistle.

Inputs: PROJECT.md, existing `weeds/sources.md`.

Steps:

1. Confirm classes: dandelion=0, clover=1, thistle=2. Grass is background.
2. Search current public sources. Update URLs and licenses; drop dead links.
3. Estimate usable RGB lawn/close-up images per class. Note if a set is only flowers or only leaves.
4. Write labeling rules: one box per plant, ignore turf, skip unreadable blur.
5. List gaps (e.g. thistle at 6–12 in AGL is scarce).
6. If the operator attached images, classify each as one of the three, `not_target`, or `unsure`, with one-line reasons. That is labeling help, not a spray decision.

Validate: licenses present. No bulk download. No extra classes.

Approval: ask before any large download.
