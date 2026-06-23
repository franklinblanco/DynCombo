/** @odoo-module **/

import { registry } from "@web/core/registry";
import {
    MonetaryField,
    monetaryField,
} from "@web/views/fields/monetary/monetary_field";

/**
 * Amount column for sale order lines: on a combo header it shows the kit's total
 * (the sum of its components) instead of the header's own subtotal, which is 0
 * in sum pricing. Display only — the underlying price_subtotal still drives the
 * column footer and the order total, so nothing is double-counted.
 */
class ComboAmountField extends MonetaryField {
    get value() {
        const data = this.props.record.data;
        if (data.combo_report_role === "parent") {
            return data.combo_display_subtotal || 0;
        }
        return super.value;
    }
}

export const comboAmountField = {
    ...monetaryField,
    component: ComboAmountField,
};

registry.category("fields").add("combo_amount", comboAmountField);
