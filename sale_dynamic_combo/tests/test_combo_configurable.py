# -*- coding: utf-8 -*-
from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestComboConfigurable(TransactionCase):
    """Configurable combos: optional components and pick-one choice groups."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({'name': 'Cfg Customer'})
        P = cls.env['product.product']
        cls.A = P.create({'name': 'CFG A required', 'type': 'consu', 'list_price': 10.0})
        cls.B = P.create({'name': 'CFG B opt-off', 'type': 'consu', 'list_price': 10.0})
        cls.C = P.create({'name': 'CFG C opt-on', 'type': 'consu', 'list_price': 10.0})
        cls.D = P.create({'name': 'CFG D colour red', 'type': 'consu', 'list_price': 10.0})
        cls.E = P.create({'name': 'CFG E colour blue', 'type': 'consu', 'list_price': 10.0})
        cls.combo = cls.env['product.template'].create({
            'name': 'CFG Combo', 'type': 'consu',
            'is_dynamic_combo': True, 'dynamic_combo_pricing': 'sum',
            'dynamic_combo_component_ids': [
                (0, 0, {'component_product_id': cls.A.id, 'quantity': 1, 'sequence': 10}),
                (0, 0, {'component_product_id': cls.B.id, 'quantity': 1, 'sequence': 20,
                        'is_optional': True, 'default_included': False}),
                (0, 0, {'component_product_id': cls.C.id, 'quantity': 1, 'sequence': 30,
                        'is_optional': True, 'default_included': True}),
                (0, 0, {'component_product_id': cls.D.id, 'quantity': 1, 'sequence': 40,
                        'choice_group': 'colour', 'default_included': True}),
                (0, 0, {'component_product_id': cls.E.id, 'quantity': 1, 'sequence': 50,
                        'choice_group': 'colour', 'default_included': False}),
            ],
        })

    def _order_with_combo(self):
        o = self.env['sale.order'].create({'partner_id': self.partner.id})
        self.env['sale.order.line'].create({
            'order_id': o.id, 'product_id': self.combo.product_variant_id.id,
            'product_uom_qty': 1})
        return o

    def test_expansion_respects_optional_and_choice(self):
        o = self._order_with_combo()
        products = o.order_line.filtered(
            lambda l: l.combo_report_role == 'component').mapped('product_id')
        self.assertIn(self.A, products, "required component is always added")
        self.assertNotIn(self.B, products, "optional default-off is skipped")
        self.assertIn(self.C, products, "optional default-on is added")
        self.assertIn(self.D, products, "choice-group default is added")
        self.assertNotIn(self.E, products, "non-default choice-group member is skipped")
        self.assertEqual(len(products), 3)

    def test_two_options_from_same_choice_group_blocked(self):
        o = self._order_with_combo()
        header = o.order_line.filtered(lambda l: l.combo_report_role == 'parent')
        with self.assertRaises(ValidationError):
            self.env['sale.order.line'].create({
                'order_id': o.id, 'product_id': self.E.id, 'product_uom_qty': 1,
                'combo_group': header.combo_group})  # second 'colour' → blocked
