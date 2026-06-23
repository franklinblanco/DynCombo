from . import models


def post_init_hook(env):
    """Backfill phantom BoMs for combos that already exist (e.g. on upgrade)."""
    combos = env['product.template'].search([('is_dynamic_combo', '=', True)])
    combos._sync_dynamic_combo_bom()
