# DynCombo — Path A Milestone (deepen Sales, justify ~$49–59)

Goal: turn DynCombo from a $30 utility into a $49–59 "premium dynamic combo for
Sales" without leaving the Sales app. Path B (POS / Website / Purchase breadth,
toward $65–69) is a **separate later milestone**.

**Agreed execution order (2026-06-23):** push → perfect the test suite → manual
browser tests → **Task 1 combo discount** → Tasks 2–4 → when v18 is *feature
complete*, port to **17.0 then 16.0** as separate branches in this publishing
repo (the section-subtotal fix lives in the version-specific sale report
template, so each port needs its own test pass). **Status: Tasks 0 & 1 DONE** —
14 tests green, combo discount verified in-browser; Tasks 2–4 next.

Sequencing rationale: Task 0 protects the price (no money-wrong PDFs); Tasks 1–2
are quick visible value; Task 3 is cheap parity; Task 4 is the big differentiator
that carries the price.

---

## Task 0 — Test suite  ← DONE (14 tests, green) (price floor, not a feature)
**Why:** we found 5 real bugs by hand, incl. a wrong PDF total. At $49+ a wrong
total = refunds + bad reviews. Lock the behaviour down so Odoo point-releases and
future features can't silently break totals.
**Scope:**
- `tests/test_combo_totals.py` — sum vs fixed pricing; header priced 0 (sum) /
  components priced 0 (fixed); combo total = component sum and **not doubled**
  (Bug 1 regression); qty rescale; `combo_report_subtotal` collapsed=total /
  detailed=0; section-subtotal mechanism = grand total (Bug 2 regression).
- `tests/test_combo_report.py` — render the QWeb report collapsed & detailed;
  assert section subtotal includes a collapsed combo and that a collapsed combo
  line shows its tax (Bug 4) and hides components (`_get_order_lines_to_report`).
- `tests/test_combo_product.py` — phantom BoM created/updated/removed in lockstep
  with components; live price/cost recompute when a component price changes.
**Files:** new `tests/` package (auto-discovered; no manifest change).
**Effort:** ~2 days. **Acceptance:** `--test-enable` green; every fixed bug has a
failing-before/passing-after test.

## Task 1 — Combo-level discount  ← DONE (v18.0.5.9.0)
Shipped: a discount on the combo header propagates to every component in sum
pricing (combo total + section subtotals drop together) and discounts the combo
price in fixed pricing; it also prints on a collapsed combo line. Reuses the
standard line `discount` field (needs the Sales *Discounts* setting). Tests:
`test_combo_discount_sum_spreads_to_components`, `test_combo_discount_fixed_on_header`.
Follow-ups: live JS recompute on the header (today it applies on save), and new
dragged-in components inheriting the combo discount.

**Why:** real quoting need; no dynamic-combo competitor does it cleanly.
**Approach:** add `combo_discount` (%) on the combo header line. In **sum**
pricing, distribute it onto the component lines' `discount` (so totals + the
phantom-BoM/procurement stay consistent and the math is transparent); in
**fixed** pricing it maps to the header's own `discount`. Surface on the order
line and show "Disc. %" on the collapsed combo row in the PDF (the cell already
exists from the Bug 4 fix).
**Files:** `models/sale_order_line.py` (field + propagation in `write`/onchange,
mirroring the existing qty-propagation), `report/sale_report_combo.xml`,
`views/sale_order_views.xml`, tests.
**Effort:** S (~1–2 d). **Risk:** low — reuses qty-propagation pattern.

## Task 2 — Margin per combo
**Why:** "see your margin live" is a strong rep-facing selling point; you already
compute live cost.
**Approach:** computed `combo_margin` / `combo_margin_pct` on the header from
`combo_display_subtotal` − Σ(component cost × qty). Optional column on the order
line; optional line in the PDF behind a setting.
**Files:** `models/sale_order_line.py`, `views/sale_order_views.xml`, tests.
**Effort:** S (~1 d). **Risk:** low (read-only, display).

## Task 3 — Per-component min/max quantity
**Why:** cheap parity with BrowseInfo's "allowed quantity ranges".
**Approach:** `min_qty` / `max_qty` on `sale.combo.component`; validate the SO
component line qty (block or warn + clamp) in `write`/constraint.
**Files:** `models/sale_combo_component.py`, `models/sale_order_line.py`,
`views/product_template_views.xml`, tests.
**Effort:** S–M (~2 d). **Risk:** low.

## Task 4 — Configurable / optional combos  ← the differentiator
**Why:** moves DynCombo into CPQ territory; this is what actually carries $59.
**Approach:** on `sale.combo.component` add `is_optional` and `choice_group`
(pick-one-of-a-group). When the combo is added to a quote, run a lightweight
configurator (wizard or inline) so the rep includes/excludes optionals and picks
one per choice group; expand only the chosen components. Live pricing already
follows whatever lines exist, so totals "just work".
**Files:** `models/sale_combo_component.py`, new `wizard/combo_configurator.py`
(+ view), `models/sale_order_line.py` (`_expand_combo_components` honours
choices), `static/src/js/combo_product_field.js`, tests.
**Effort:** L (~1–2 wk). **Risk:** medium — new UX surface; needs solid tests
(hence Task 0 first).

---

### Milestone exit criteria
- All tasks have tests; suite green on 18.0.
- Listing updated: feature matrix incl. discount/margin/ranges/configurator;
  fresh screenshots + short demo video.
- Bump to 18.0.6.0.0, raise price to $49 (then $59 after configurator + a few
  reviews).

### Path B (later milestone, toward $65–69)
Website/eCommerce combos (biggest differentiator vs the €139 all-in-one), then
POS, then deeper Purchase. Tracked separately.
