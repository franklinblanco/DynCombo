/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component, xml } from "@odoo/owl";
import { standardFieldProps } from "@web/views/fields/standard_field_props";

/**
 * Tiny leading-column widget that visualises the combo nesting on each line:
 * a "↳" branch icon on combo components and a "▾" marker on combo headers, so
 * the indentation of a kit and its parts is obvious at a glance. Derived from
 * the live client-side data (combo_group / is_dynamic_combo), so it updates the
 * instant a line is dragged in or out of a combo — no save / refresh needed.
 */
class ComboIndentField extends Component {
    static props = { ...standardFieldProps };
    static template = xml`
        <span class="o_dyncombo_indent" style="display:inline-block;min-width:1.2em;text-align:center;">
            <t t-if="role === 'component'">
                <span class="text-muted" style="font-weight:bold;padding-left:10px;" title="Combo component">&#8627;</span>
            </t>
            <t t-elif="role === 'header'">
                <span class="text-muted" title="Combo">&#9662;</span>
            </t>
        </span>`;

    get role() {
        const d = this.props.record.data;
        if (d.is_dynamic_combo && d.combo_group) {
            return "header";
        }
        if (d.combo_group && !d.is_dynamic_combo) {
            return "component";
        }
        return "normal";
    }
}

export const comboIndentField = {
    component: ComboIndentField,
};

registry.category("fields").add("combo_indent", comboIndentField);
