/** @odoo-module */


import { formatMonetary } from "@web/views/fields/formatters";
import { parseFloat } from "@web/views/fields/parsers";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { useService } from "@web/core/utils/hooks";
import { registry } from "@web/core/registry";
// this.orm = useService("orm");
import {
    formatFloat,
    humanNumber,
    insertThousandsSep,
} from "@web/core/utils/numbers";
import { formatCurrency as  formatCurrencyNumber, getCurrency } from "@web/core/currency";
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
import { TaxTotalsComponent } from "@account/components/tax_totals/tax_totals";
import { patch } from "@web/core/utils/patch";

// export class ProductLine extends Component {
//         setup() {
//         super.setup();
//         this.pos = usePos();
//         this.popup = useService("popup")
//         this.orm = useService("orm")
//         this.state = useState({
//         // product: this.props.product
//         });
//         onWillStart(async () => {
//                 await this.format_value();
//             });
//         }
  
// }
patch(TaxTotalsComponent.prototype, {

       
        setup() {
            this.orm = useService("orm");
            super.setup();
           
            // this.formatData();
        },

    // async format_value(value) {
    //     var result=0;
    //     let result = await this.orm.call("account.journal", "format_value", [value]);
    //     value = result;
               
                
    // },
        
    async formatData(props) {
        // this.orm = useService("orm");
        // let orm=this.orm;
        const currency = getCurrency(props.record.data.currency_id);
        
        let totals = JSON.parse(JSON.stringify(toRaw(props.record.data[this.props.name])));
        if (!totals) {
            return;
        }
        const currencyFmtOpts = { currencyId: props.record.data.currency_id && props.record.data.currency_id[0] };
        const digits = currencyFmtOpts.digits || (currency && currency.digits);
        const symbol = currencyFmtOpts.symbol;
        var result=0;
        let amount_untaxed = totals.amount_untaxed;
        let amount_tax = 0;
        let subtotals = [];
        for (let subtotal_title of totals.subtotals_order) {
            
            let amount_total = amount_untaxed + amount_tax
            // let value=amount_total
            // let result = await this.orm.call("account.journal", "format_value", [value]);
           
            let remain = amount_total - Math.trunc(amount_total)
            if (Math.trunc(remain*100) == 0){
                amount_total= Math.trunc(amount_total)}
            else{
                amount_total= Math.trunc(amount_total)+ (Math.trunc(remain*100)/100)}
            // 
            subtotals.push({
                'name': subtotal_title,
                'amount': amount_total,
                'formatted_amount': getCurrency(this.currencyId).symbol + '' + amount_total.toLocaleString(),
            
                // formatMonetary(amount_total, currencyFmtOpts),
                                
            });
            let group = totals.groups_by_subtotal[subtotal_title];
            for (let i in group) {
                amount_tax = amount_tax + group[i].tax_group_amount;
            }
        }
        totals.subtotals = subtotals;
        let rounding_amount = totals.display_rounding && totals.rounding_amount || 0;
        let amount_total = amount_untaxed + amount_tax + rounding_amount;

        let remain = amount_total - Math.trunc(amount_total)
        if (Math.trunc(remain*100) == 0){
            amount_total= Math.trunc(amount_total)}
        else{
            amount_total= Math.trunc(amount_total)+ (Math.trunc(remain*100)/100)}
        
        totals.amount_total = amount_total.toLocaleString();
        totals.formatted_amount_total = getCurrency(this.currencyId).symbol + ' ' + amount_total.toLocaleString();
        // formatMonetary(amount_total, currencyFmtOpts);
       
        
        for (let group_name of Object.keys(totals.groups_by_subtotal)) {
            let group = totals.groups_by_subtotal[group_name];
            for (let key in group) {
                group[key].formatted_tax_group_amount = formatMonetary(group[key].tax_group_amount, currencyFmtOpts);
                group[key].formatted_tax_group_base_amount = formatMonetary(group[key].tax_group_base_amount, currencyFmtOpts);
            }
        }
        this.totals = totals;
    }
    
})
// tax_totals.formatData() = this.formatData();
// registry.add("remove_decimal_zero_trailing", TaxTotalsCustom);
// registry.category("fields").add("tax_totals_custom", TaxTotalsCustom);