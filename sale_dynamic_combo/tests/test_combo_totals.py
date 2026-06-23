# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestComboTotals(TransactionCase):
    """Locks down the combo pricing/total behaviour — every assertion here maps
    to a bug we hit in production (totals doubling, collapsed-print subtotals)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({'name': 'DynCombo Test Customer'})
        P = cls.env['product.product']
        cls.stand = P.create({'name': 'DC Stand', 'type': 'consu',
                              'list_price': 45.0, 'standard_price': 30.0})
        cls.mouse = P.create({'name': 'DC Mouse', 'type': 'consu',
                              'list_price': 25.0, 'standard_price': 15.0})
        cls.hub = P.create({'name': 'DC Hub', 'type': 'consu',
                            'list_price': 60.0, 'standard_price': 40.0})

        def comps():
            return [
                (0, 0, {'component_product_id': cls.stand.id, 'quantity': 1}),
                (0, 0, {'component_product_id': cls.mouse.id, 'quantity': 1}),
                (0, 0, {'component_product_id': cls.hub.id, 'quantity': 1}),
            ]
        T = cls.env['product.template']
        cls.sum_combo = T.create({
            'name': 'DC Sum Combo', 'type': 'consu',
            'is_dynamic_combo': True, 'dynamic_combo_pricing': 'sum',
            'dynamic_combo_component_ids': comps(),
        })
        cls.fixed_combo = T.create({
            'name': 'DC Fixed Combo', 'type': 'consu', 'list_price': 200.0,
            'is_dynamic_combo': True, 'dynamic_combo_pricing': 'fixed',
            'dynamic_combo_component_ids': comps(),
        })

    # helpers ----------------------------------------------------------------
    def _order(self):
        return self.env['sale.order'].create({'partner_id': self.partner.id})

    def _add(self, order, variant, qty=1.0):
        return self.env['sale.order.line'].create({
            'order_id': order.id, 'product_id': variant.id, 'product_uom_qty': qty,
        })

    def _header(self, order):
        return order.order_line.filtered(lambda l: l.combo_report_role == 'parent')

    def _components(self, order):
        return order.order_line.filtered(lambda l: l.combo_report_role == 'component')

    # Bug 1 — combo total must equal the component sum, never doubled ---------
    def test_sum_combo_total_not_doubled(self):
        order = self._order()
        self._add(order, self.sum_combo.product_variant_id)
        header = self._header(order)
        self.assertEqual(len(header), 1)
        self.assertEqual(header.combo_display_subtotal, 130.0,
                         "combo total must be the component sum (45+25+60), not doubled")
        self.assertEqual(header.price_subtotal, 0.0,
                         "a sum-priced combo header carries no price of its own")
        self.assertEqual(order.amount_untaxed, 130.0)

    def test_sum_combo_total_stable_after_flush(self):
        order = self._order()
        self._add(order, self.sum_combo.product_variant_id)
        order.flush_recordset()
        self.env.invalidate_all()
        self.assertEqual(self._header(order).combo_display_subtotal, 130.0)

    def test_sum_combo_qty_scales_components_and_total(self):
        order = self._order()
        self._add(order, self.sum_combo.product_variant_id, qty=2.0)
        self.assertEqual(sum(self._components(order).mapped('product_uom_qty')), 6.0)
        self.assertEqual(self._header(order).combo_display_subtotal, 260.0)
        self.assertEqual(order.amount_untaxed, 260.0)

    # fixed pricing: money on the header, components zeroed -------------------
    def test_fixed_combo_prices_header_only(self):
        order = self._order()
        self._add(order, self.fixed_combo.product_variant_id)
        header = self._header(order)
        self.assertEqual(header.price_subtotal, 200.0)
        self.assertEqual(header.combo_display_subtotal, 200.0)
        self.assertTrue(all(c.price_subtotal == 0.0 for c in self._components(order)))
        self.assertEqual(order.amount_untaxed, 200.0)

    # Bug 2 — collapsed combo still counts toward its section subtotal --------
    def test_combo_report_subtotal_per_mode(self):
        order = self._order()
        self._add(order, self.sum_combo.product_variant_id)
        header = self._header(order)
        order.combo_print_full = False           # collapsed
        self.assertTrue(header.combo_parent_show_total)
        self.assertEqual(header.combo_report_subtotal, 130.0)
        order.combo_print_full = True            # detailed
        self.assertFalse(header.combo_parent_show_total)
        self.assertEqual(header.combo_report_subtotal, 0.0)

    def test_section_subtotal_equals_grand_total_both_modes(self):
        order = self._order()
        self._add(order, self.sum_combo.product_variant_id)      # 130
        extra = self.env['product.product'].create(
            {'name': 'DC Extra', 'type': 'consu', 'list_price': 490.0})
        self._add(order, extra)                                  # 490
        for full in (False, True):
            order.combo_print_full = full
            reported = order._get_order_lines_to_report()
            section_total = sum(reported.mapped('combo_report_subtotal'))
            self.assertEqual(section_total, 620.0,
                             "section subtotal must reconcile with the grand "
                             "total (combo_print_full=%s)" % full)
            self.assertEqual(order.amount_untaxed, 620.0)

    # Path A — combo-level discount -----------------------------------------
    def test_combo_discount_sum_spreads_to_components(self):
        order = self._order()
        self._add(order, self.sum_combo.product_variant_id)
        header = self._header(order)
        header.discount = 10.0
        self.assertTrue(all(c.discount == 10.0 for c in self._components(order)),
                        "a discount on the combo header applies to every component")
        self.assertAlmostEqual(header.combo_display_subtotal, 117.0)  # 130 * 0.9
        self.assertAlmostEqual(order.amount_untaxed, 117.0)

    def test_combo_discount_fixed_on_header(self):
        order = self._order()
        self._add(order, self.fixed_combo.product_variant_id)
        header = self._header(order)
        header.discount = 25.0
        self.assertAlmostEqual(header.price_subtotal, 150.0)  # 200 * 0.75
        self.assertAlmostEqual(order.amount_untaxed, 150.0)
        # components stay zero-priced, so their discount can't affect the total
        self.assertEqual(sum(self._components(order).mapped('price_subtotal')), 0.0)

    # Path A — combo margin (rep-facing) ------------------------------------
    def test_combo_margin_on_header(self):
        order = self._order()
        self._add(order, self.sum_combo.product_variant_id)
        header = self._header(order)
        # revenue 130 ; cost 30+15+40 = 85 ; margin 45
        self.assertAlmostEqual(header.combo_cost_subtotal, 85.0)
        self.assertAlmostEqual(header.combo_margin, 45.0)
        self.assertAlmostEqual(header.combo_margin_pct, 34.62, places=2)  # 45/130

    def test_combo_margin_follows_discount(self):
        order = self._order()
        self._add(order, self.sum_combo.product_variant_id)
        header = self._header(order)
        header.discount = 10.0           # revenue 117, cost still 85
        self.assertAlmostEqual(header.combo_margin, 32.0)
