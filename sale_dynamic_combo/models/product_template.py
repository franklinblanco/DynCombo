from odoo import api, fields, models


class ProductProduct(models.Model):
    _inherit = 'product.product'

    def get_dynamic_combo_components(self):
        """Component descriptors for the sales widget to add as order lines when
        a dynamic combo product is selected. Called by combo_product_field.js."""
        self.ensure_one()
        return [{
            'product_id': comp.component_product_id.id,
            'display_name': comp.component_product_id.display_name,
            'quantity': comp.quantity,
            'unit_qty': comp.quantity,
        } for comp in self.dynamic_combo_component_ids]


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    # Namespaced as "dynamic_combo" so it never collides with Odoo's built-in
    # POS "combo" product type / is_combo concept.
    is_dynamic_combo = fields.Boolean(
        string="Dynamic Combo",
        help="When enabled, adding this product to a quotation expands it into "
             "its component products. The composition can be edited per quote "
             "and printed collapsed (combo only) or in full detail. On purchase "
             "and in inventory the kit is exploded into its components.",
    )
    dynamic_combo_pricing = fields.Selection(
        selection=[
            ('sum', "Sum of components"),
            ('fixed', "Fixed combo price"),
        ],
        string="Combo Pricing",
        default='sum',
        help="Sum of components: the combo price is the live total of its "
             "components and updates as you edit them on the quotation.\n"
             "Fixed combo price: the combo is sold at this product's own sales "
             "price; components are informational only.",
    )
    dynamic_combo_component_ids = fields.One2many(
        'sale.combo.component', 'product_tmpl_id',
        string="Combo Components",
        copy=True,
    )

    # --- live pricing & cost -------------------------------------------------
    # These never go stale: they are recomputed from the *current* component
    # values every time they are read. This is the whole point of the module —
    # native Odoo kits freeze the kit's price/cost when the kit is created.
    dynamic_combo_price = fields.Float(
        string="Live Combo Price",
        compute='_compute_dynamic_combo_amounts',
        digits='Product Price',
        help="Sum of the current sales prices of the components. Shown for "
             "reference; in 'Sum of components' pricing this is what the combo "
             "sells for on a quotation.",
    )
    dynamic_combo_cost = fields.Float(
        string="Live Combo Cost",
        compute='_compute_dynamic_combo_amounts',
        digits='Product Price',
        help="Sum of the current costs (standard_price) of the components. "
             "Follows component cost changes automatically — e.g. when import "
             "freight pushes a component cost up, the kit cost moves with it.",
    )

    @api.depends(
        'dynamic_combo_component_ids.quantity',
        'dynamic_combo_component_ids.component_product_id.list_price',
        'dynamic_combo_component_ids.component_product_id.standard_price',
    )
    def _compute_dynamic_combo_amounts(self):
        for tmpl in self:
            price = cost = 0.0
            for comp in tmpl.dynamic_combo_component_ids:
                product = comp.component_product_id
                price += product.list_price * comp.quantity
                cost += product.standard_price * comp.quantity
            tmpl.dynamic_combo_price = price
            tmpl.dynamic_combo_cost = cost

    # --- native phantom BoM sync ---------------------------------------------
    # We lean on Odoo's proven phantom Bill of Materials for the inventory and
    # purchase sides: a kit with a phantom BoM is exploded into its components
    # on receipt (purchase_mrp), on delivery, and in valuation. We keep that BoM
    # in lockstep with the combo's component list so the user maintains the
    # composition in one place (the Combo / Kit tab).
    dynamic_combo_bom_id = fields.Many2one(
        'mrp.bom', string="Combo Kit BoM", copy=False, readonly=True,
        help="Phantom Bill of Materials generated from the combo components. "
             "Drives the explosion into components on purchase and in inventory.",
    )

    def _sync_dynamic_combo_bom(self):
        """Create/update/remove the phantom BoM mirroring the components.

        Runs as sudo so users who can edit products but lack MRP rights can
        still maintain combos.
        """
        Bom = self.env['mrp.bom'].sudo()
        for tmpl in self:
            components = tmpl.dynamic_combo_component_ids
            if tmpl.is_dynamic_combo and components:
                line_cmds = [(5, 0, 0)] + [
                    (0, 0, {
                        'product_id': comp.component_product_id.id,
                        'product_qty': comp.quantity,
                    })
                    for comp in components
                ]
                if tmpl.dynamic_combo_bom_id:
                    tmpl.dynamic_combo_bom_id.write({
                        'type': 'phantom',
                        'bom_line_ids': line_cmds,
                    })
                else:
                    bom = Bom.create({
                        'product_tmpl_id': tmpl.id,
                        'type': 'phantom',
                        'product_qty': 1.0,
                        'bom_line_ids': line_cmds,
                    })
                    tmpl.with_context(
                        combo_skip_bom_sync=True
                    ).dynamic_combo_bom_id = bom.id
            elif tmpl.dynamic_combo_bom_id:
                # No longer a combo (or no components left): drop the BoM.
                tmpl.dynamic_combo_bom_id.unlink()

    @api.model_create_multi
    def create(self, vals_list):
        templates = super().create(vals_list)
        templates._sync_dynamic_combo_bom()
        return templates

    def write(self, vals):
        res = super().write(vals)
        if not self.env.context.get('combo_skip_bom_sync') and (
            {'is_dynamic_combo', 'dynamic_combo_component_ids'} & set(vals)
        ):
            self._sync_dynamic_combo_bom()
        return res
