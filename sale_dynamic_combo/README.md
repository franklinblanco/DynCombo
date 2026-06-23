# Dynamic Combos & Kits for Quotations

Quote bundles of products like QuickBooks "group items": define a product made
of several components, **edit the composition per quotation**, and **print
either the combo alone or the full breakdown**.

This is the first productization target from the production-Odoo issue list
(dad's request: *"crear kits o combos dinámicos para poder cotizar … se pueda
cambiar al momento de cotizar … al imprimirlo se pueda solo imprimir el combo o
todo el detalle"*).

## How it works

1. **Mark a product as a combo** — Product form → *Combo / Kit* tab → tick
   *Dynamic Combo / Kit*, choose pricing, and list the default components.
2. **Quote it** — add the combo to a quotation. It expands into its component
   lines, which you can edit, swap, or re-quantify for that specific quote.
3. **Print it** — set *Print Mode* on the combo line.

### Pricing (per combo product)

| Mode | Combo line | Component lines | Order total |
|------|-----------|-----------------|-------------|
| **Sum of components** | header, price 0, shows live total | carry the prices | sum of components |
| **Fixed combo price** | carries the price | informational, price 0 | the combo price |

**Live price & cost — never stale.** On the *Combo / Kit* tab the product shows
a **Live Combo Price** (sum of the components' current sales prices) and a
**Live Combo Cost** (sum of the components' current `standard_price`). Both are
computed from the *current* component values every time, so when a component's
cost moves — e.g. import freight rises — the kit follows automatically. This is
the gap in native Odoo kits, where the kit price/cost is frozen at creation and
must be re-edited by hand.

### Purchase & inventory (components, not the kit)

Marking a product as a dynamic combo generates and maintains a **phantom Bill of
Materials** (kept in lockstep with the component list). Because of that:

- **Buying** the kit on a purchase order receives its **components** into stock,
  not one opaque "kit" product (via `purchase_mrp`).
- **Inventory valuation** is on the components, at their current cost.
- On a quotation the kit is delivered through its expanded component lines; the
  combo header line itself does not procure, so components are never delivered
  twice.

### Print modes (per quotation line)

| Mode | On the PDF |
|------|------------|
| **Combo only** | one bundled line showing the combo total |
| **Full detail (no component prices)** | combo total + components with quantities only |
| **Full detail (with component prices)** | itemized components (sum pricing only) |

### Document-wide print control

For a large quote (e.g. 200 lines, 20 combos) you don't have to set each combo
line. Two options drive the whole document:

- **Two print actions** in the order's *Print* menu — **combos collapsed** (hide
  all components) and **full detail** (show all) — resolve it in one click,
  overriding every line's own mode.
- A **Combo Detail on Print** field on the order (*per combo* / *collapsed* /
  *detailed*) for when you'd rather set it on the document and print normally.

These layer on top of the per-line mode (highest priority: the print action,
then the document field, then each line's own setting).

## Design notes / current limitations

- Components are real `sale.order.line` records linked via
  `combo_parent_line_id`, so all standard editing works. They appear **live**
  when you add the combo (an onchange expands it — no save or page refresh), and
  combo headers are shown in bold with their components tinted.
- The purchase/inventory explosion is delegated to Odoo's native **phantom
  BoM** (`mrp` + `sale_mrp` + `purchase_mrp` dependencies). The BoM is generated
  and resynced automatically from the *Combo / Kit* components — do not edit it
  by hand; it is overwritten on the next component change.
- Per-quote composition edits (swapping/adding components on a specific
  quotation) affect that quotation's delivery only. The purchase explosion uses
  the product's default composition (the phantom BoM), which is the standard
  Odoo behaviour for buying a kit.
- Per-quote composition is fully editable: change a component's quantity or
  price, delete a component, or **add** one by adding a product line and setting
  its **Combo** column (an optional column on the order lines) to the combo
  header. A guided "add component" button is still a possible future polish.
- Component prices only render in *detail_with_prices* under **sum** pricing
  (under fixed pricing components have no individual price).
- With **fixed** pricing and an invoice policy of *delivered quantities*, the
  combo header line does not procure (delivery happens through the components),
  so verify the invoicing flow for that combination against the customer's Odoo
  before shipping.

## Licensing

DynCombo is a **commercial, paid product**: a proprietary module sold via the
Odoo Apps store (and/or directly). Introductory launch price **10.00 USD** in
the manifest (planned to rise to $15 after launch).
Built clean (no OCA code) and marked **OPL-1** so it can be sold. Target the
customer's exact Odoo version before distributing — prototyped on 18.0.

Three legal files ship in the module root and travel with every copy:

- **LICENSE** — the Odoo Proprietary License v1.0 (forbids redistribution,
  sublicensing, and resale).
- **COPYRIGHT** — the copyright / ownership notice OPL-1 refers to.
- **EULA.txt** — the plain-language end-user agreement (no redistribution; a
  hosting provider may run it only on the customer's behalf), with a Spanish
  courtesy summary.

The EULA is a practical template, not legal advice — have it reviewed by a
lawyer before commercial distribution.
