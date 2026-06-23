import uuid

from odoo import api, fields, models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    # --- structure -----------------------------------------------------------
    # The invisible grouping key. A combo header owns a unique value; every line
    # that belongs to that combo carries the same value. This is a plain char, so
    # it persists across a save (unlike a Many2one to a not-yet-saved sibling
    # line, which was the root of the live-update trouble). The drag widget sets
    # and clears it; combo_parent_line_id is then derived from it server-side.
    combo_group = fields.Char(copy=False, index=True)
    combo_color = fields.Integer(
        compute='_compute_combo_color', store=True,
        help="Per-combo colour index (0 = not in a combo), so combos are easy "
             "to tell apart in the order lines.")
    # Derived from combo_group: the combo header line this line belongs to. Stored
    # and recomputed, so it is always correct after a save (real ids), and all the
    # pricing / report / delivery logic can keep keying off it.
    combo_parent_line_id = fields.Many2one(
        'sale.order.line', string="Combo",
        compute='_compute_combo_parent_line_id', store=True, index=True,
        help="The combo this line is a component of.")
    combo_component_line_ids = fields.One2many(
        'sale.order.line', 'combo_parent_line_id', string="Combo Components",
    )
    # Quantity of this component per ONE unit of the parent combo. Used to
    # re-scale components when the combo quantity changes, while still letting
    # the user override a component quantity by hand.
    combo_unit_qty = fields.Float(
        string="Qty per Combo", default=1.0,
        digits='Product Unit of Measure',
    )
    # Mirrors of product fields the JS widgets read (combo headers, pricing).
    is_dynamic_combo = fields.Boolean(
        related='product_id.is_dynamic_combo', readonly=True)
    dynamic_combo_pricing = fields.Selection(
        related='product_id.dynamic_combo_pricing', readonly=True)

    # --- report / UI helpers (computed, not stored) --------------------------
    combo_report_role = fields.Selection(
        selection=[
            ('normal', "Normal"),
            ('parent', "Combo"),
            ('component', "Component"),
        ],
        compute='_compute_combo_report_fields',
    )
    combo_display_subtotal = fields.Monetary(
        string="Combo Total",
        compute='_compute_combo_report_fields',
        currency_field='currency_id',
        help="The amount shown for the combo header line: the sum of its "
             "components (sum pricing) or its own price (fixed pricing).",
    )
    combo_parent_show_total = fields.Boolean(
        compute='_compute_combo_report_fields',
    )
    # Per-line amount a printed section subtotal should add up. Mirrors what the
    # line actually shows in its subtotal cell, so a collapsed combo (whose money
    # sits on hidden component lines) still counts toward its section total.
    combo_report_subtotal = fields.Monetary(
        compute='_compute_combo_report_fields',
        currency_field='currency_id',
    )
    combo_hide_price_in_report = fields.Boolean(
        compute='_compute_combo_report_fields',
    )
    # True for the lines whose price we force to zero (combo header in sum
    # pricing, components in fixed pricing) — used to make the price read-only.
    combo_price_locked = fields.Boolean(
        compute='_compute_combo_report_fields',
    )

    # --- grouping (combo_group -> parent line & colour) ----------------------
    @api.depends('combo_group', 'is_dynamic_combo',
                 'order_id.order_line.combo_group',
                 'order_id.order_line.is_dynamic_combo')
    def _compute_combo_parent_line_id(self):
        for line in self:
            parent = False
            if line.combo_group and not line.is_dynamic_combo:
                header = line.order_id.order_line.filtered(
                    lambda l: l.is_dynamic_combo
                    and l.combo_group == line.combo_group)
                parent = header[:1].id if header else False
            line.combo_parent_line_id = parent

    @api.depends('combo_group',
                 'order_id.order_line.combo_group',
                 'order_id.order_line.is_dynamic_combo')
    def _compute_combo_color(self):
        for line in self:
            order = line.order_id
            # Order-independent (sorted by the group key, not sequence) so a
            # drag/reorder never changes a combo's colour or leaves it stale.
            headers = order.order_line.filtered('is_dynamic_combo').sorted(
                lambda l: l.combo_group or '')
            groups = []
            for header in headers:
                if header.combo_group and header.combo_group not in groups:
                    groups.append(header.combo_group)
            if line.combo_group and line.combo_group in groups:
                line.combo_color = (groups.index(line.combo_group) % 11) + 1
            else:
                line.combo_color = 0

    def _combo_effective_print_mode(self):
        """Print mode in force: the order's 'Combo Detail on Print' scope —
        show the full combo (with components) or just the combo line."""
        self.ensure_one()
        if self.order_id.combo_print_full:
            return 'detail_with_prices'
        return 'combo_only'

    @api.depends(
        'product_id', 'combo_parent_line_id', 'combo_group',
        'price_subtotal',
        'order_id.order_line.price_subtotal',
        'order_id.order_line.combo_group',
        'order_id.order_line.is_dynamic_combo',
        'order_id.combo_print_full',
        'combo_parent_line_id.order_id.combo_print_full',
    )
    def _compute_combo_report_fields(self):
        for line in self:
            product = line.product_id
            parent = line.combo_parent_line_id
            is_parent = bool(product.is_dynamic_combo) and not parent

            # role
            if is_parent:
                line.combo_report_role = 'parent'
            elif parent:
                line.combo_report_role = 'component'
            else:
                line.combo_report_role = 'normal'

            # amount displayed on a combo header line
            if is_parent and product.dynamic_combo_pricing == 'sum':
                # Sum the component lines straight off the order, keyed by the
                # combo group. The combo_component_line_ids One2many can't be
                # trusted here: during the combo's create/expand its inverse
                # cache transiently holds each component twice (a pre-flush
                # NewId and its saved id), which would double the total.
                components = line.order_id.order_line.filtered(
                    lambda l, g=line.combo_group: g and l.combo_group == g
                    and not l.is_dynamic_combo)
                line.combo_display_subtotal = sum(
                    components.mapped('price_subtotal'))
            elif is_parent:
                line.combo_display_subtotal = line.price_subtotal
            else:
                line.combo_display_subtotal = 0.0

            # Component prices are only meaningful in "sum" pricing, and only
            # shown when the effective print mode explicitly asks for them.
            if is_parent:
                mode = line._combo_effective_print_mode()
                show_component_prices = (
                    mode == 'detail_with_prices'
                    and product.dynamic_combo_pricing == 'sum'
                )
                line.combo_parent_show_total = not show_component_prices
                line.combo_hide_price_in_report = False
                line.combo_price_locked = (
                    product.dynamic_combo_pricing == 'sum')
            elif parent:
                mode = parent._combo_effective_print_mode()
                show_component_prices = (
                    mode == 'detail_with_prices'
                    and parent.product_id.dynamic_combo_pricing == 'sum'
                )
                line.combo_parent_show_total = False
                line.combo_hide_price_in_report = not show_component_prices
                line.combo_price_locked = (
                    parent.product_id.dynamic_combo_pricing == 'fixed')
            else:
                line.combo_parent_show_total = False
                line.combo_hide_price_in_report = False
                line.combo_price_locked = False

            # What this row contributes to a printed section subtotal. A combo
            # header contributes its combo total only when collapsed (components
            # hidden); when expanded it contributes 0 and the visible components
            # carry the money. Everything else contributes its own subtotal.
            if is_parent:
                line.combo_report_subtotal = (
                    line.combo_display_subtotal
                    if line.combo_parent_show_total else 0.0)
            else:
                line.combo_report_subtotal = line.price_subtotal

    # --- pricing -------------------------------------------------------------
    def _compute_price_unit(self):
        super()._compute_price_unit()
        for line in self:
            product = line.product_id
            # In "sum" pricing the money lives on the component lines, so the
            # combo header itself is priced at zero (it's a title + total).
            if (product.is_dynamic_combo and not line.combo_parent_line_id
                    and product.dynamic_combo_pricing == 'sum'):
                line.price_unit = 0.0
            # In "fixed" pricing the money lives on the combo header, so the
            # component lines are zero-priced (informational).
            elif (line.combo_parent_line_id
                  and line.combo_parent_line_id.product_id.dynamic_combo_pricing
                  == 'fixed'):
                line.price_unit = 0.0

    # --- expansion & propagation --------------------------------------------
    # Live kit-quantity rescale is done client-side by combo_qty_field.js (an
    # onchange updates the components server-side but the web client doesn't
    # reflect those sibling changes live). write() below stays the save / API
    # backstop.

    @api.model_create_multi
    def create(self, vals_list):
        lines = super().create(vals_list)
        # Give every new combo header a unique group id (its own).
        for line in lines:
            if line.is_dynamic_combo and not line.combo_group:
                line.combo_group = uuid.uuid4().hex
        if not self.env.context.get('combo_no_expand'):
            for line in lines:
                if (line.is_dynamic_combo and not line.display_type
                        and not line.combo_component_line_ids
                        # Skip if components for this combo are already in the
                        # batch (same group) — avoids double expansion.
                        and not any(other.combo_group == line.combo_group
                                    and other != line for other in lines)):
                    line._expand_combo_components()
        # Safety net: a sum-priced combo header carries no price (money is on the
        # components); the client can optimistically send the list price.
        for line in lines:
            if (line.is_dynamic_combo and not line.combo_parent_line_id
                    and line.product_id.dynamic_combo_pricing == 'sum'
                    and line.price_unit):
                line.price_unit = 0.0
        # A combo header created already carrying a discount (import / API)
        # spreads it to its components, same as write() does on edit.
        for line in lines:
            if (line.is_dynamic_combo and not line.combo_parent_line_id
                    and line.discount
                    and line.product_id.dynamic_combo_pricing == 'sum'):
                components = line.order_id.order_line.filtered(
                    lambda l, g=line.combo_group: g and l.combo_group == g
                    and not l.is_dynamic_combo)
                for child in components:
                    if child.discount != line.discount:
                        child.with_context(
                            combo_no_propagate=True).discount = line.discount
        return lines

    def write(self, vals):
        res = super().write(vals)
        if self.env.context.get('combo_no_propagate'):
            return res
        # Propagate quantity changes between a combo and its components.
        if 'product_uom_qty' in vals:
            for line in self:
                if (line.product_id.is_dynamic_combo
                        and not line.combo_parent_line_id
                        and line.combo_component_line_ids):
                    for child in line.combo_component_line_ids:
                        new_qty = child.combo_unit_qty * line.product_uom_qty
                        if child.product_uom_qty != new_qty:
                            child.with_context(
                                combo_no_propagate=True
                            ).write({'product_uom_qty': new_qty})
                elif line.combo_parent_line_id:
                    parent_qty = line.combo_parent_line_id.product_uom_qty or 1.0
                    line.with_context(combo_no_propagate=True).combo_unit_qty = (
                        line.product_uom_qty / parent_qty)
        # Propagate a combo header's discount across its components, so one
        # discount on the combo header discounts the whole combo. Sum pricing
        # only — fixed pricing carries the money (and the discount) on the
        # header itself, and the components are zero-priced.
        if 'discount' in vals:
            for line in self:
                if (line.product_id.is_dynamic_combo
                        and not line.combo_parent_line_id
                        and line.product_id.dynamic_combo_pricing == 'sum'):
                    for child in line.combo_component_line_ids:
                        if child.discount != line.discount:
                            child.with_context(
                                combo_no_propagate=True
                            ).write({'discount': line.discount})
        return res

    def _expand_combo_components(self):
        """Create editable component lines from the combo's default components,
        tagged with the combo's group so they belong to it."""
        self.ensure_one()
        components = self.product_id.dynamic_combo_component_ids
        if not components:
            return
        vals_list = [{
            'order_id': self.order_id.id,
            'product_id': comp.component_product_id.id,
            'product_uom_qty': comp.quantity * (self.product_uom_qty or 1.0),
            'combo_unit_qty': comp.quantity,
            'combo_group': self.combo_group,
            'sequence': self.sequence,
        } for comp in components]
        self.env['sale.order.line'].with_context(
            combo_no_expand=True).create(vals_list)

    # --- delivery ------------------------------------------------------------
    def _action_launch_stock_rule(self, previous_product_uom_qty=False):
        """The combo header doesn't procure on a quotation — its component lines
        do (and the phantom BoM handles purchase/standalone stock). This avoids
        delivering the components twice."""
        header_lines = self.filtered(
            lambda l: l.product_id.is_dynamic_combo
            and not l.combo_parent_line_id
            and l.combo_component_line_ids
        )
        remaining = self - header_lines
        if not remaining:
            return True
        return super(SaleOrderLine, remaining)._action_launch_stock_rule(
            previous_product_uom_qty=previous_product_uom_qty)
