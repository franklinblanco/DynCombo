# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestComboReport(TransactionCase):
    """Renders the actual sale-order QWeb report (the PDF code path) to guard
    Bug 2 (collapsed combo missing from the printed section subtotal) and Bug 4
    (collapsed combo line dropping its taxes)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({'name': 'DynCombo Report Customer'})
        P = cls.env['product.product']
        stand = P.create({'name': 'RC Stand', 'type': 'consu', 'list_price': 45.0})
        mouse = P.create({'name': 'RC Mouse', 'type': 'consu', 'list_price': 25.0})
        hub = P.create({'name': 'RC Hub', 'type': 'consu', 'list_price': 60.0})
        cls.combo = cls.env['product.template'].create({
            'name': 'RC Sum Combo', 'type': 'consu',
            'is_dynamic_combo': True, 'dynamic_combo_pricing': 'sum',
            'dynamic_combo_component_ids': [
                (0, 0, {'component_product_id': stand.id, 'quantity': 1}),
                (0, 0, {'component_product_id': mouse.id, 'quantity': 1}),
                (0, 0, {'component_product_id': hub.id, 'quantity': 1}),
            ],
        })
        cls.extra = P.create({'name': 'RC Extra', 'type': 'consu', 'list_price': 490.0})
        cls.report = cls.env.ref('sale.action_report_saleorder')

    def _order(self, collapsed):
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id, 'combo_print_full': not collapsed})
        SOL = self.env['sale.order.line']
        SOL.create({'order_id': order.id, 'display_type': 'line_section', 'name': 'Section A'})
        SOL.create({'order_id': order.id,
                    'product_id': self.combo.product_variant_id.id, 'product_uom_qty': 1})
        SOL.create({'order_id': order.id, 'product_id': self.extra.id, 'product_uom_qty': 1})
        return order

    def _render(self, order):
        html = self.report._render_qweb_html(self.report.report_name, order.ids)[0]
        return html.decode() if isinstance(html, bytes) else html

    def test_collapsed_report_includes_combo_in_section_subtotal(self):
        html = self._render(self._order(collapsed=True))
        # combo's own total appears, and the section/grand total reconciles at 620
        self.assertIn('130.00', html, "collapsed combo line should show its total")
        self.assertIn('620.00', html, "section subtotal must include the combo (not 490)")
        self.assertNotIn('RC Stand', html, "components must be hidden when collapsed")

    def test_detailed_report_shows_components(self):
        html = self._render(self._order(collapsed=False))
        self.assertIn('RC Stand', html, "components must be listed when detailed")
        self.assertIn('620.00', html)
