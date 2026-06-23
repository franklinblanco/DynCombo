{
    'name': "DynCombo — Dynamic Kits & Combos for Sales",
    'summary': "DynCombo: build kits/combos that price themselves live, "
               "drag products in/out, edit per quote, print collapsed or "
               "detailed, and explode into components on purchase and inventory.",
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

Three print modes per quotation line: combo only, full detail without component
prices, or full detail with component prices.

Available in English and Spanish.
""",
    'author': "Franklin Blanco",
    'support': "me@franklinblanco.dev",
    'website': "https://franklinblanco.dev",
    'category': 'Sales/Sales',
    'version': '18.0.5.5.0',
    'license': 'OPL-1',
    'price': 89.00,
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
        ],
    },
    'images': ['static/description/banner.png'],
    'post_init_hook': 'post_init_hook',
    'installable': True,
    'application': False,
}
