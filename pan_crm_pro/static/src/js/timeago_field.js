/** @odoo-module **/
import { Component } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { formatDateTime } from "@web/core/l10n/dates";

export class TimeagoField extends Component {
    static props = { ...standardFieldProps };
    static template = "pan_crm_pro.TimeagoField";

    get relativeString() {
        const value = this.props.record.data[this.props.name];
        if (!value) {
            return "";
        }
        return value.toRelative();
    }

    get formattedValue() {
        const value = this.props.record.data[this.props.name];
        if (!value) {
            return "";
        }
        return formatDateTime(value);
    }
}

export const timeagoField = {
    component: TimeagoField,
    displayName: _t("Time Ago"),
    supportedTypes: ["datetime"],
};

registry.category("fields").add("timeago", timeagoField);
