import re

from odoo import api, models, fields


class AccountAccount(models.Model):
    _inherit = "account.account"
    _description = "Account"

    internal_group = fields.Selection(
        selection_add=[('cost_of_revenue', 'Cost of Revenue')],
    )
    @api.depends('account_type')
    def _compute_internal_group(self):
        for account in self:
            if account.account_type:
                if account.account_type == 'off_balance':
                    account.internal_group = 'off_balance'
                elif account.account_type == 'expense_direct_cost':
                    account.internal_group = 'cost_of_revenue'
                else :
                    account.internal_group = account.account_type.split('_')[0]


