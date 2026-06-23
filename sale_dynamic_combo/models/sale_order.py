from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    combo_print_full = fields.Boolean(
        string="Show full combo on print",
        default=True, copy=True,
        help="Print the full breakdown of every combo (its components). "
             "Untick to print just the combo line.",
    )

    def _normalize_combo_order(self):
        """Keep combos flat: each combo's components sit right under their header
        and combos never interleave with each other or with stray lines. Runs on
        save, so however the lines were dragged, combos end up as clean blocks."""
        for order in self:
            lines = order.order_line.sorted(lambda l: (l.sequence, l.id))
            if not lines.filtered('is_dynamic_combo'):
                continue
            ordered = []
            placed = set()
            for line in lines:
                if line.id in placed:
                    continue
                if line.is_dynamic_combo:
                    ordered.append(line)
                    placed.add(line.id)
                    for comp in lines.filtered(
                            lambda l: l.combo_parent_line_id == line
                            and l.id not in placed):
                        ordered.append(comp)
                        placed.add(comp.id)
                elif line.combo_parent_line_id:
                    continue  # a component: emitted right after its header
                else:
                    ordered.append(line)
                    placed.add(line.id)
            # anything left (e.g. a component whose header is gone) keeps its spot
            for line in lines:
                if line.id not in placed:
                    ordered.append(line)
                    placed.add(line.id)
            if [line.id for line in ordered] != lines.ids:
                seq = 10
                for line in ordered:
                    if line.sequence != seq:
                        # Direct assignment: a line write (not an order write, so
                        # no normalize recursion) and, in the onchange path, an
                        # in-memory change the client applies.
                        line.sequence = seq
                    seq += 10

    # Live reordering after a drag is done client-side by combo_drag.js (an
    # onchange can change the sequence values but the web client won't re-sort
    # the rows from it). This write-time normalize is the save/API backstop.

    @api.model_create_multi
    def create(self, vals_list):
        orders = super().create(vals_list)
        orders._normalize_combo_order()
        return orders

    def write(self, vals):
        res = super().write(vals)
        if 'order_line' in vals and not self.env.context.get('combo_no_normalize'):
            self._normalize_combo_order()
        return res

    def _get_order_lines_to_report(self):
        lines = super()._get_order_lines_to_report()
        # Drop component lines whose combo prints collapsed — driven by the
        # combo's effective print mode (per-line setting, the document-wide
        # scope, or a report-time override).
        return lines.filtered(
            lambda line: not (
                line.combo_parent_line_id
                and line.combo_parent_line_id._combo_effective_print_mode()
                == 'combo_only'
            )
        )
