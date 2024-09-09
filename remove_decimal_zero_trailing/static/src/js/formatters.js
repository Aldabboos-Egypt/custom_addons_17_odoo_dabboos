/** @odoo-module **/

import { localization as l10n } from "@web/core/l10n/localization";
import { registry } from "@web/core/registry";
import { escape, intersperse, nbsp, sprintf } from "@web/core/utils/strings";
import { session } from "@web/session";
import { markup } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { MonetaryField } from "@web/views/fields/monetary/monetary_field";
import { patch } from "@web/core/utils/patch";
import {
    formatFloat as formatFloatNumber,
    humanNumber,
    insertThousandsSep,
} from "@web/core/utils/numbers";
import { formatCurrency as  formatCurrencyNumber, getCurrency } from "@web/core/currency";

export function formatFloat(value, options = {}) {
    if (value === false) {
        return "";
    }

    if (options.humanReadable) {
        return humanNumber(value, options);
    }
    const grouping = options.grouping || l10n.grouping;
    const thousandsSep = "thousandsSep" in options ? options.thousandsSep : l10n.thousandsSep;
    const decimalPoint = "decimalPoint" in options ? options.decimalPoint : l10n.decimalPoint;
    let precision;
    if (options.digits && options.digits[1] !== undefined) {
        precision = options.digits[1];
    } else {
        precision = 2;
    }
    const formatted = (value || 0).toFixed(precision).split(".");
    formatted[0] = insertThousandsSep(formatted[0], thousandsSep, grouping);
    formatted[1] = formatted[1].replace(/0+$/, "");
    if (options.trailingZeros === false && formatted[1]) {
        formatted[1] = formatted[1].replace(/0+$/, "");
    }
//    console.log(formatted[0]);
//    console.log(formatted[1]);
    return formatted[1] ? formatted.join(decimalPoint) : formatted[0];
}

registry.category("formatters").remove("float")
registry
    .category("formatters")
    .add("float", formatFloat)

export function formatCurrency(amount, currencyId, options = {}) {
    const currency = getCurrency(currencyId);
    const digits = options.digits || (currency && currency.digits);

    let formattedAmount;
    if (options.humanReadable) {
        formattedAmount = humanNumber(amount, { decimals: digits ? digits[1] : 2 });
    } else {
        formattedAmount = formatFloat(amount, { digits });
    }

    if (!currency || options.noSymbol) {
        return formattedAmount;
    }
    const formatted = [currency.symbol, formattedAmount];
    if (currency.position === "after") {
        formatted.reverse();
    }
    console.log(formatted);
    return formatted.join(nbsp);
}

export function formatMonetary(value, options = {}) {
    // Monetary fields want to display nothing when the value is unset.
    // You wouldn't want a value of 0 euro if nothing has been provided.
    if (value === false) {
        return "";
    }

    let currencyId = options.currencyId;
    if (!currencyId && options.data) {
        const currencyField =
            options.currencyField ||
            (options.field && options.field.currency_field) ||
            "currency_id";
        const dataValue = options.data[currencyField];
        currencyId = Array.isArray(dataValue) ? dataValue[0] : dataValue;
    }
    return formatCurrency(value, currencyId, options)
}

registry.category("formatters").remove("monetary")
registry.category("formatters").add("monetary", formatMonetary)

//to override Monetary widget -- it use formatMonetary
patch(MonetaryField.prototype, {
        get formattedValue() {
        if (this.props.inputType === "number" && !this.props.readonly && this.value) {

            return this.value;
        }
//        console.log(this.value);
        return formatMonetary(this.value, {
            digits: this.currencyDigits,
            currencyId: this.currencyId,
            noSymbol: !this.props.readonly || this.props.hideSymbol,
        });
    }
})