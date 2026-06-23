"""The 'Combo Detail on Print' selection (combo_print_scope) became a checkbox
(combo_print_full). Carry the value over before the old column is dropped:
collapsed -> unchecked, everything else -> checked (show full combo)."""


def migrate(cr, version):
    if not version:
        return
    cr.execute(
        "SELECT 1 FROM information_schema.columns "
        "WHERE table_name = 'sale_order' AND column_name = 'combo_print_scope'"
    )
    if cr.fetchone():
        cr.execute(
            "ALTER TABLE sale_order ADD COLUMN IF NOT EXISTS combo_print_full boolean"
        )
        cr.execute(
            "UPDATE sale_order "
            "SET combo_print_full = (combo_print_scope IS DISTINCT FROM 'collapsed')"
        )
