/** @odoo-module **/

import { registry } from "@web/core/registry";
import { FloatField, floatField } from "@web/views/fields/float/float_field";
import { useEffect } from "@odoo/owl";

/**
 * Quantity field for sale order lines that rescales a kit's components live when
 * the kit's quantity changes — client-side, so the components update on screen
 * without a save (a server onchange can't push sibling-line changes to the web
 * client). Each component's qty = combo_unit_qty * kit qty. No-op on non-kit
 * lines, so it's safe to use for the whole column.
 */
class ComboQtyField extends FloatField {
    setup() {
        super.setup();
        useEffect(
            () => this._rescaleComponents(),
            () => [this.value]
        );
    }

    _rescaleComponents() {
        const record = this.props.record;
        if (!record.data.is_dynamic_combo || !record.data.combo_group) {
            return;
        }
        const list = record.model.root.data.order_line;
        if (!list) {
            return;
        }
        const qty = this.value || 0;
        const group = record.data.combo_group;
        for (const comp of list.records) {
            if (
                comp.id === record.id ||
                comp.data.is_dynamic_combo ||
                comp.data.combo_group !== group
            ) {
                continue;
            }
            const newQty = (comp.data.combo_unit_qty || 0) * qty;
            if (comp.data.product_uom_qty !== newQty) {
                comp.update({ product_uom_qty: newQty });
            }
        }
    }
}

export const comboQtyField = {
    ...floatField,
    component: ComboQtyField,
};

registry.category("fields").add("combo_qty", comboQtyField);
