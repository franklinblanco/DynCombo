from odoo import api, fields, models


class SaleComboComponent(models.Model):
    """A default component of a combo product, configured on the product itself.

    These are the *template* of the combo. When the combo is added to a
    quotation they are copied into editable sale order lines, so the actual
    composition can still be changed for that specific quote. They also drive a
    generated phantom BoM that handles the purchase/inventory explosion.
    """
    _name = 'sale.combo.component'
    _description = "Dynamic Combo Component"
    _order = 'sequence, id'

    product_tmpl_id = fields.Many2one(
        'product.template', string="Combo Product",
        required=True, ondelete='cascade', index=True,
    )
    sequence = fields.Integer(default=10)
    component_product_id = fields.Many2one(
        'product.product', string="Component", required=True,
    )
    quantity = fields.Float(
        string="Quantity", default=1.0, required=True,
        digits='Product Unit of Measure',
    )
    # Read-only mirrors of the component product's current sale price and cost,
    # shown on the Combo / Kit tab so the user can see the breakdown. They track
    # the product, so they update when the component's price/cost changes.
    component_price = fields.Float(
        string="Unit Price", related='component_product_id.list_price',
        readonly=True, digits='Product Price',
    )
    component_cost = fields.Float(
        string="Unit Cost", related='component_product_id.standard_price',
        readonly=True, digits='Product Price',
    )
    # Per-row contribution to the combo total (qty * unit). Summed in the list
    # footer so the columns reconcile with the Live Combo Price / Cost.
    component_price_subtotal = fields.Float(
        string="Price Subtotal", compute='_compute_component_subtotals',
        digits='Product Price',
    )
    component_cost_subtotal = fields.Float(
        string="Cost Subtotal", compute='_compute_component_subtotals',
        digits='Product Price',
    )

    @api.depends('quantity', 'component_price', 'component_cost')
    def _compute_component_subtotals(self):
        for comp in self:
            comp.component_price_subtotal = comp.quantity * comp.component_price
            comp.component_cost_subtotal = comp.quantity * comp.component_cost

    # Keep the generated phantom BoM in sync when components are maintained
    # directly (not only through the product form's one2many write).
    @api.model_create_multi
    def create(self, vals_list):
        components = super().create(vals_list)
        components.product_tmpl_id._sync_dynamic_combo_bom()
        return components

    def write(self, vals):
        res = super().write(vals)
        self.product_tmpl_id._sync_dynamic_combo_bom()
        return res

    def unlink(self):
        templates = self.product_tmpl_id
        res = super().unlink()
        templates._sync_dynamic_combo_bom()
        return res
