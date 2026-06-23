/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { uuid } from "@web/views/utils";
import { SaleOrderLineProductField } from "@sale/js/sale_product_field";

/**
 * When a "Dynamic Combo / Kit" product is set on a sale order line, add its
 * component products as editable lines right away — client-side, so they show
 * live without saving (same approach the drag uses).
 *
 * The header is tagged with a unique combo_group; the components share it. The
 * server derives combo_parent_line_id from the group and, seeing the components
 * already supplied for this group, skips its own expansion (no doubles).
 */
patch(SaleOrderLineProductField.prototype, {
    async _onProductUpdate() {
        await super._onProductUpdate(...arguments);
        const record = this.props.record;
        const productId = record.data.product_id;
        if (!record.data.is_dynamic_combo || !productId) {
            return;
        }

        const orderLines = record.model.root.data.order_line;

        // Already expanded (e.g. the update fired again)? -> do nothing.
        const existing = record.data.combo_group;
        if (
            existing &&
            orderLines.records.some(
                (r) => r.id !== record.id && r.data.combo_group === existing
            )
        ) {
            return;
        }

        // Give the header a group id the components will share.
        let group = existing;
        if (!group) {
            group = uuid();
            await record.update({ combo_group: group });
        }

        const components = await this.orm.call(
            "product.product",
            "get_dynamic_combo_components",
            [productId[0]],
            { context: this.context }
        );

        const headerQty = record.data.product_uom_qty || 1;
        for (const comp of components) {
            const line = await orderLines.addNewRecord({
                position: "bottom",
                mode: "readonly",
            });
            await line._update({
                product_id: [comp.product_id, comp.display_name],
                product_uom_qty: comp.quantity * headerQty,
                combo_unit_qty: comp.unit_qty,
                combo_group: group,
                sequence: record.data.sequence,
            });
        }
        // Place the components next to their header.
        await orderLines._sort?.();
        orderLines.leaveEditMode?.();

        // In sum pricing the money lives on the components, so the header shows
        // no price. Done last — after the components are added — so it can't
        // interrupt the expansion the way an earlier price write did.
        if (record.data.dynamic_combo_pricing === "sum" && record.data.price_unit) {
            await record.update({ price_unit: 0 });
        }
    },
});
