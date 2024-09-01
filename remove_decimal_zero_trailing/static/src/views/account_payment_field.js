/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { usePopover } from "@web/core/popover/popover_hook";
import { useService } from "@web/core/utils/hooks";
import { localization } from "@web/core/l10n/localization";
import { parseDate, formatDate } from "@web/core/l10n/dates";
import { patch } from "@web/core/utils/patch";

import { formatMonetary } from "@web/views/fields/formatters";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
// import { Component } from "@odoo/owl";
import { AccountPaymentField } from "@account/components/account_payment_field/account_payment_field";

import {
    Component,
    onPatched,
    onWillUpdateProps,
    onWillRender,
    toRaw,
    mount,
    useRef,
    useState,
} from "@odoo/owl";

patch(AccountPaymentField.prototype, {
    
       
    setup() {
        // this.orm = useService("orm");
        // super.setup();
//         super.setup();
//     //     // this.orm = useService("orm");
//     //     // this.action = useService("action");
        
const position = localization.direction === "rtl" ? "bottom" : "left";
    // this.popover = usePopover(AccountPaymentPopOver, { position });
    this.orm = useService("orm");
    this.action = useService("action");
      
    },

// export class AccountPaymentField extends Component {
    // static props = { ...standardFieldProps };

    // setup() {
    //     const position = localization.direction === "rtl" ? "bottom" : "left";
    //     this.popover = usePopover(AccountPaymentPopOver, { position });
    //     this.orm = useService("orm");
    //     this.action = useService("action");
    // },

    getInfo() 
    {
        // static props = { ...standardFieldProps };
        const info = this.props.record.data[this.props.name] || {
            content: [],
            outstanding: false,
            title: "",
            move_id: this.props.record.resId,
        };
        for (const [key, value] of Object.entries(info.content)) {
            value.index = key;
            value.amount_formatted = value.amount.toLocaleString();
            // formatMonetary(value.amount, {
            //     currencyId: value.currency_id,
            // });
            if (value.date) {
                // value.date is a string, parse to date and format to the users date format
                value.date = formatDate(parseDate(value.date));
            }
        }
        return {
            lines: info.content,
            outstanding: info.outstanding,
            title: info.title,
            moveId: info.move_id,
        };
    }
})
