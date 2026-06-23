/** @odoo-module **/

import { registry } from "@web/core/registry";
import { FloatField, floatField } from "@web/views/fields/float/float_field";
import { useEffect } from "@odoo/owl";

/**
 * Discount field for sale order lines: when the discount on a sum-priced combo
 * header changes, it applies the same discount to every component line live,
 * client-side, so the combo total updates without a save (a server onchange
 * can't push sibling-line changes to the web client). No-op on non-kit lines and
 * on fixed-priced combos (whose money is on the header), so it is safe to use
 * for the whole column. The save-time write() stays the API / backstop.
 */
class ComboDiscountField extends FloatField {
    setup() {
        super.setup();
        useEffect(
            () => this._propagateDiscount(),
            () => [this.value]
        );
    }

    _propagateDiscount() {
        const record = this.props.record;
        if (!record.data.is_dynamic_combo || !record.data.combo_group) {
            return;
        }
        if (record.data.dynamic_combo_pricing !== "sum") {
            return;
        }
        const list = record.model.root.data.order_line;
        if (!list) {
            return;
        }
        const discount = this.value || 0;
        const group = record.data.combo_group;
        for (const comp of list.records) {
            if (
                comp.id === record.id ||
                comp.data.is_dynamic_combo ||
                comp.data.combo_group !== group
            ) {
                continue;
            }
            if (comp.data.discount !== discount) {
                comp.update({ discount: discount });
            }
        }
    }
}

export const comboDiscountField = {
    ...floatField,
    component: ComboDiscountField,
};

registry.category("fields").add("combo_discount", comboDiscountField);
