{
    'name': "DynCombo — Dynamic Kits & Combos for Sales",
    'summary': "DynCombo: kits/combos that price themselves live (price, cost & "
               "margin), configurable per deal with optional & choice-group "
               "components, combo-wide discounts, quantity guardrails, collapsed "
               "or detailed printing, and exploded into components on purchase "
               "& inventory.",
    'description': """
DynCombo — Dynamic Kits & Combos
================================

Define a product as a combo made of several component products. When you add it
to a quotation it expands into editable component lines, so you can change the
composition for that specific quote. On the printed PDF you choose, per combo,
whether to show only the combo or the full breakdown of components.

Pricing is configurable per combo: a fixed combo price, or the live sum of its
components. The combo price and cost are recomputed from the *current* component
values every time — they never go stale the way native Odoo kits do when a
component price changes (e.g. moving import freight costs).

On the purchase and inventory side the combo is backed by a generated phantom
Bill of Materials, so buying or stocking the kit is recognised as its
components, not as a single opaque product.

Sell smarter per deal:
* Live combo margin (price - cost), on the product and on every quote line
  (rep-facing, never on the customer PDF).
* One discount on the combo applies to the whole combo.
* Min/max quantity per component, enforced per combo.
* Configurable combos: optional components and pick-one choice groups
  (e.g. colour or size).

Print collapsed (combo only) or in full detail with one tick - section
subtotals, taxes and discounts always reconcile with the order total.

Fully translated in English, Spanish, Italian, Portuguese and French. Built for
Odoo 18.0, with 17.0 and 16.0 on the way — the goal is to support every active
Odoo version.
""",
    'author': "Franklin Blanco",
    'support': "me@franklinblanco.dev",
    'website': "https://apps.odoo.com/apps/modules/18.0/sale_dynamic_combo",
    'category': 'Sales/Sales',
    'version': '18.0.5.12.3',
    'license': 'OPL-1',
    'price': 70.00,
    'currency': 'USD',
    'depends': ['sale_management', 'mrp', 'sale_mrp', 'purchase_mrp'],
    'data': [
        'security/ir.model.access.csv',
        'views/product_template_views.xml',
        'views/sale_order_views.xml',
        'report/sale_report_combo.xml',
    ],
    'demo': [
        'demo/combo_demo.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'sale_dynamic_combo/static/src/js/combo_product_field.js',
            'sale_dynamic_combo/static/src/js/combo_drag.js',
            'sale_dynamic_combo/static/src/js/combo_amount_field.js',
            'sale_dynamic_combo/static/src/js/combo_qty_field.js',
            'sale_dynamic_combo/static/src/js/combo_discount_field.js',
        ],
    },
    'images': ['static/description/banner.png'],
    'post_init_hook': 'post_init_hook',
    'installable': True,
    'application': False,
}
