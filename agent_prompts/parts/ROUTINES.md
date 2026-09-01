# Routines for `parts`

Create only after one manual `refresh-bom` looks right. Test run first.

## Weekly price check (safe)

Paste to `parts`:

> Every Monday at 09:00 in my local timezone, run the refresh-bom skill.
> Update `/workspace/weed-spray/bom/current.csv` and `cap.md`.
> Post in this conversation: total, gap vs $500, and any SKU that went out of stock.
> Do not sign in, do not check out, do not email vendors.
> If a product page is unavailable, keep the old row, mark `in_stock=unknown`, and say so.

## Do not create

- Auto-buy when price drops
- Anything that submits a cart
