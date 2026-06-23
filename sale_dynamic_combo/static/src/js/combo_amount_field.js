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
 *
 * In sum pricing the total is summed from the component lines *live*, so it
 * tracks quantity/discount edits without a save: the server-side
 * combo_display_subtotal depends on sibling lines, and a web-client onchange
 * doesn't recompute one line's field when a different line changes.
 */
class ComboAmountField extends MonetaryField {
    get value() {
        const record = this.props.record;
        const data = record.data;
        if (data.combo_report_role === "parent") {
            if (data.dynamic_combo_pricing === "sum" && data.combo_group) {
                const list = record.model.root.data.order_line;
                if (list) {
                    let total = 0;
                    for (const comp of list.records) {
                        if (
                            comp.id !== record.id &&
                            !comp.data.is_dynamic_combo &&
                            comp.data.combo_group === data.combo_group
                        ) {
                            total += comp.data.price_subtotal || 0;
                        }
                    }
                    return total;
                }
            }
            // fixed pricing (header carries its own price) or no list: the
            // stored total already tracks the header's own edits live.
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
