# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestComboProduct(TransactionCase):
    """The product side: live (never-stale) combo price/cost and the phantom
    BoM kept in lockstep with the component list."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        P = cls.env['product.product']
        cls.a = P.create({'name': 'CP A', 'type': 'consu',
                          'list_price': 100.0, 'standard_price': 60.0})
        cls.b = P.create({'name': 'CP B', 'type': 'consu',
                          'list_price': 40.0, 'standard_price': 25.0})
        cls.combo = cls.env['product.template'].create({
            'name': 'CP Combo', 'type': 'consu',
            'is_dynamic_combo': True, 'dynamic_combo_pricing': 'sum',
            'dynamic_combo_component_ids': [
                (0, 0, {'component_product_id': cls.a.id, 'quantity': 2}),
                (0, 0, {'component_product_id': cls.b.id, 'quantity': 1}),
            ],
        })

    def test_live_price_and_cost(self):
        # price = 2*100 + 1*40 = 240 ; cost = 2*60 + 1*25 = 145
        self.assertAlmostEqual(self.combo.dynamic_combo_price, 240.0)
        self.assertAlmostEqual(self.combo.dynamic_combo_cost, 145.0)

    def test_live_margin(self):
        self.assertAlmostEqual(self.combo.dynamic_combo_margin, 95.0)  # 240 - 145

    def test_live_price_follows_component_price_change(self):
        self.a.list_price = 120.0
        self.combo.invalidate_recordset()
        self.assertAlmostEqual(self.combo.dynamic_combo_price, 280.0)  # 2*120 + 40

    def test_phantom_bom_created_and_grows_with_components(self):
        bom = self.combo.dynamic_combo_bom_id
        self.assertTrue(bom, "a combo with components generates a phantom BoM")
        self.assertEqual(bom.type, 'phantom')
        self.assertEqual(len(bom.bom_line_ids), 2)
        c = self.env['product.product'].create(
            {'name': 'CP C', 'type': 'consu', 'list_price': 10.0})
        self.env['sale.combo.component'].create({
            'product_tmpl_id': self.combo.id,
            'component_product_id': c.id, 'quantity': 1})
        self.combo.invalidate_recordset()
        self.assertEqual(len(self.combo.dynamic_combo_bom_id.bom_line_ids), 3)

    def test_phantom_bom_removed_when_no_longer_a_combo(self):
        self.assertTrue(self.combo.dynamic_combo_bom_id)
        self.combo.is_dynamic_combo = False
        self.combo.invalidate_recordset()
        self.assertFalse(self.combo.dynamic_combo_bom_id,
                         "dropping the combo flag removes its phantom BoM")
