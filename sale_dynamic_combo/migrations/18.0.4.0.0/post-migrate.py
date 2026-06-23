"""The combo print control changed from three options (per_line/collapsed/
detailed) to two (detailed/collapsed). Convert orders still holding the old
'per_line' value (or none) to the new default, 'detailed' (show full combo).

Raw SQL + a column-exists guard so this stays safe even when run as part of a
multi-version upgrade where combo_print_scope was later replaced."""


def migrate(cr, version):
    if not version:
        return
    cr.execute(
        "SELECT 1 FROM information_schema.columns "
        "WHERE table_name = 'sale_order' AND column_name = 'combo_print_scope'"
    )
    if cr.fetchone():
        cr.execute(
            "UPDATE sale_order SET combo_print_scope = 'detailed' "
            "WHERE combo_print_scope IS NULL OR combo_print_scope = 'per_line'"
        )
