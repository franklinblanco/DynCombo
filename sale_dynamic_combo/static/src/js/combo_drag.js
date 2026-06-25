/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { ListRenderer } from "@web/views/list/list_renderer";
import { Dialog } from "@web/core/dialog/dialog";
import { _t } from "@web/core/l10n/translation";
import { Component, xml } from "@odoo/owl";

/** Small 3-choice dialog for deleting a kit. */
class ComboDeleteDialog extends Component {
    static components = { Dialog };
    static template = xml`
        <Dialog title="title" size="'md'">
            <t t-esc="body"/>
            <t t-set-slot="footer">
                <button class="btn btn-primary" t-on-click="() => this.pick('all')" t-esc="labelAll"/>
                <button class="btn btn-secondary" t-on-click="() => this.pick('kit')" t-esc="labelKit"/>
                <button class="btn btn-secondary" t-on-click="() => this.props.close()" t-esc="labelCancel"/>
            </t>
        </Dialog>`;
    static props = { close: Function, onChoice: Function };
    title = _t("Delete kit");
    body = _t(
        "This is a kit. Do you want to delete the kit together with its " +
        "components, or only the kit (keeping its components as separate lines)?"
    );
    labelAll = _t("Kit and its components");
    labelKit = _t("Only the kit");
    labelCancel = _t("Cancel");
    pick(choice) {
        this.props.onChoice(choice);
        this.props.close();
    }
}

patch(ListRenderer.prototype, {
    /** Remember the dragged row's original predecessor, to revert an illegal move. */
    sortStart(params) {
        super.sortStart(params);
        const el = params && params.element;
        const prev = el && el.previousElementSibling;
        this._comboDragOrigPrevId = prev ? prev.dataset.id : null;
    },

    async sortDrop(dataRowId, params) {
        await super.sortDrop(dataRowId, params);

        const list = this.props.list;
        if (!list) {
            return;
        }
        const dragged = list.records.find((r) => r.id === dataRowId);
        if (!dragged || !("combo_group" in dragged.data)) {
            return; // not our list
        }

        const prevId =
            params && params.previous ? params.previous.dataset.id : null;
        const prev = prevId ? list.records.find((r) => r.id === prevId) : null;

        if (dragged.data.is_dynamic_combo) {
            // A kit dropped *inside* another kit (its components continue below
            // the drop point) is not allowed — bounce it back where it was.
            const draggedIdx = list.records.findIndex((r) => r.id === dragged.id);
            const otherGroup = prev && prev.data.combo_group;
            const insideOther =
                otherGroup &&
                otherGroup !== dragged.data.combo_group &&
                list.records
                    .slice(draggedIdx + 1)
                    .some((r) => r.data.combo_group === otherGroup);
            if (insideOther) {
                await list.resequence(dragged.id, this._comboDragOrigPrevId);
            }
        } else {
            // A normal line joins the combo of the line above it (or leaves).
            const newGroup = (prev && prev.data.combo_group) || false;
            const oldGroup = dragged.data.combo_group || false;
            if (oldGroup !== newGroup) {
                if (newGroup) {
                    // Joining a combo: rescale this line's quantity by the kit's
                    // quantity and apply the kit's discount, live — so it shows
                    // without a save (the qty / discount widgets only react to
                    // the header's own edits, not to a new member arriving).
                    const header = list.records.find(
                        (r) =>
                            r.data.is_dynamic_combo &&
                            r.data.combo_group === newGroup
                    );
                    const headerQty =
                        (header && header.data.product_uom_qty) || 1;
                    // Treat the line's current qty as "per combo" (or keep its
                    // existing per-combo qty when moving between combos).
                    const unit =
                        (oldGroup && dragged.data.combo_unit_qty) ||
                        dragged.data.product_uom_qty ||
                        1;
                    const updates = {
                        combo_group: newGroup,
                        combo_unit_qty: unit,
                        product_uom_qty: unit * headerQty,
                    };
                    if (header && header.data.dynamic_combo_pricing === "sum") {
                        updates.discount = header.data.discount || 0;
                    }
                    await dragged.update(updates);
                } else {
                    // Leaving every combo: back to a standalone line.
                    await dragged.update({ combo_group: false, combo_unit_qty: 1 });
                }
            }
        }

        // Refresh colours client-side so a drag in/out recolours immediately.
        await this._recolorCombos(list);
        await this._normalizeCombos(list);
    },

    /**
     * Recompute each line's combo colour index client-side, mirroring the
     * server _compute_combo_color, so dragging a line in or out of a combo
     * recolours the rows live (the stored field would only refresh on save).
     */
    async _recolorCombos(list) {
        const headers = list.records
            .filter((r) => r.data.is_dynamic_combo)
            .sort((a, b) =>
                (a.data.combo_group || "").localeCompare(b.data.combo_group || "")
            );
        const groups = [];
        for (const h of headers) {
            const g = h.data.combo_group;
            if (g && !groups.includes(g)) {
                groups.push(g);
            }
        }
        for (const r of list.records) {
            const g = r.data.combo_group;
            const color =
                g && groups.includes(g) ? (groups.indexOf(g) % 11) + 1 : 0;
            if (r.data.combo_color !== color) {
                await r.update({ combo_color: color });
            }
        }
    },

    /** Prompt when deleting a kit header: delete it with or without its components. */
    async onDeleteRecord(record) {
        const list = this.props.list;
        const group = record.data && record.data.combo_group;
        const isKit =
            record.data && record.data.is_dynamic_combo && group &&
            list.records.some(
                (r) => r.id !== record.id && r.data.combo_group === group
            );
        if (!isKit) {
            return super.onDeleteRecord(record);
        }
        this.env.services.dialog.add(ComboDeleteDialog, {
            onChoice: async (choice) => {
                const components = list.records.filter(
                    (r) => r.id !== record.id && r.data.combo_group === group
                );
                if (choice === "all") {
                    for (const c of components) {
                        await list.delete(c);
                    }
                } else {
                    // Keep components, but detach them from the (deleted) kit.
                    for (const c of components) {
                        await c.update({ combo_group: false });
                    }
                }
                await list.delete(record);
            },
        });
    },

    /**
     * Reorder the list so each combo is a contiguous block (header then its
     * components) and combos don't interleave. Moves only rows that are out of
     * place. Mirrors SaleOrder._normalize_combo_order.
     */
    async _normalizeCombos(list) {
        const records = [...list.records];
        const hasHeaderFor = (group) =>
            records.some(
                (r) => r.data.is_dynamic_combo && r.data.combo_group === group
            );

        const desired = [];
        const placed = new Set();
        for (const r of records) {
            if (placed.has(r.id)) {
                continue;
            }
            if (r.data.is_dynamic_combo) {
                desired.push(r);
                placed.add(r.id);
                const group = r.data.combo_group;
                if (group) {
                    for (const c of records) {
                        if (
                            !placed.has(c.id) &&
                            !c.data.is_dynamic_combo &&
                            c.data.combo_group === group
                        ) {
                            desired.push(c);
                            placed.add(c.id);
                        }
                    }
                }
            } else if (r.data.combo_group && hasHeaderFor(r.data.combo_group)) {
                continue; // a component: placed right after its header above
            } else {
                desired.push(r);
                placed.add(r.id);
            }
        }
        for (const r of records) {
            if (!placed.has(r.id)) {
                desired.push(r);
                placed.add(r.id);
            }
        }

        let prevId = null;
        for (const r of desired) {
            const current = list.records.findIndex((x) => x.id === r.id);
            const target = prevId
                ? list.records.findIndex((x) => x.id === prevId) + 1
                : 0;
            if (current !== target) {
                await list.resequence(r.id, prevId);
            }
            prevId = r.id;
        }
    },
});
