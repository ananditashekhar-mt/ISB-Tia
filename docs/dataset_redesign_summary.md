# Threadly — Dataset Redesign Summary

**What we did:** Rebuilt the sample data so it looks and behaves like a real apparel store, with customers, orders, products, shipping history and policies all properly connected — and covers the real-world situations we need to demo and test (delays, partial deliveries, damaged/wrong items, returns, exchanges, cancellations).

## What changed

- **Added a real customer list** (134 customers with name, city, email, phone) instead of guessing customer identity from order details.
- **Every order now has a delivery timeline** — placed, shipped, in transit, out for delivery, delivered (or delayed/cancelled) — with dates and locations, instead of just a single status word.
- **Added realistic problem scenarios to real orders**, matched to the kind of support conversations we already test with: 2 damaged items, 12 wrong items, 10 quality issues, 10 partial deliveries (customer got 1 of 2 items). These aren't random — they match the same orders our existing test conversations already talk about, so the story is consistent.
- **Fixed a gap:** the old sample data had zero orders in a "just placed, not yet shipped" state, which meant the "cancel my order" feature could never actually succeed in a demo. Added 12 such orders so cancellation can be shown working end to end.
- **Tia's answers are now more specific** — e.g., order-tracking replies now mention the last real delivery scan instead of a generic "status unavailable" line.

## What did NOT change

- No existing order IDs, customer names, or product data were removed or renumbered — everything old still works.
- The 400 reference test conversations used for evaluation were left untouched (only linked to the right customer for traceability).
- Business rules (return window, exchange eligibility, escalation rules) were not changed.

## Verification done

- Ran the full automated test suite — accuracy unchanged (75.8%), confirming nothing broke.
- Manually tested: order tracking, a damaged-item order, a partial-delivery order, and cancelling one of the new orders — all worked as expected in the live app.
- Also smoke-tested with a local Ollama model to confirm it works outside the free "Demo" mode.

## Files touched

- `data/customers.json` — new
- `data/orders.json`, `data/support_conversations.json` — enriched (no old data removed)
- `agent.py`, `app.py` — small updates so the app uses the new, richer data
- `scripts/build_dataset.py` — new, the script that generated the above (so it's repeatable/auditable, not a one-off manual edit)
