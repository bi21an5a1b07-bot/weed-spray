Save this as a skill named **refresh-bom**. Enable it on the `parts` Bot.

When to use: operator asks for a BOM, a price check, a cheaper alternative, or whether the $500 cap still holds.

Inputs: `/workspace/weed-spray/PROJECT.md`, last `bom/current.csv` if any.

Steps:

1. Open the existing CSV if present; keep the same categories.
2. Re-open each product URL. Record unit price, stock, and ship-to-US.
3. Replace missing SKUs with the next-cheapest PX4-compatible part. Note substitutions.
4. Recompute line totals and tax/shipping estimate.
5. Keep rangefinder + optical flow + ELRS + PX4 FC + 12V pump in the list even if over cap.
6. Write `bom/current.csv` and `bom/cap.md`.
7. In chat: total, gap vs $500, top 3 cost drivers, any UART/voltage conflicts.

Validate: every row has a URL. Cap file matches the CSV sum. No checkout.

Approval: stop. Never place an order.
