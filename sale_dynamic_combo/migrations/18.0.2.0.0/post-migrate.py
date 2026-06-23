"""Backfill phantom BoMs when upgrading from a version that had no inventory
integration (<= 18.0.1.x). post_init_hook only runs on a fresh install, so the
upgrade path needs its own backfill for combos that already exist.
"""
from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    if not version:
        return
    env = api.Environment(cr, SUPERUSER_ID, {})
    combos = env['product.template'].search([('is_dynamic_combo', '=', True)])
    combos._sync_dynamic_combo_bom()
