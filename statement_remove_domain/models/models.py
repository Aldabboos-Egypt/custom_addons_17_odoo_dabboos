# -*- coding: utf-8 -*-

from odoo import models, api, _, fields
from odoo.osv import expression
from collections import defaultdict
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF, SQL
import math
from odoo.tools.misc import formatLang, format_date as odoo_format_date, get_lang

def group_by_journal(vals_list):
    res = defaultdict(list)
    for vals in vals_list:
        res[vals['journal_id']].append(vals)
    return res

class account_journal(models.Model):
    _inherit = "account.journal"


    def _fill_bank_cash_dashboard_data(self, dashboard_data):
        """Populate all bank and cash journal's data dict with relevant information for the kanban card."""
        bank_cash_journals = self.filtered(lambda journal: journal.type in ('bank', 'cash'))
        if not bank_cash_journals:
            return

        # Number to reconcile
        self._cr.execute("""
            SELECT st_line_move.journal_id,
                   COUNT(st_line.id)
              FROM account_bank_statement_line st_line
              JOIN account_move st_line_move ON st_line_move.id = st_line.move_id
             WHERE st_line_move.journal_id IN %s
               AND NOT st_line.is_reconciled
               AND st_line_move.to_check IS NOT TRUE
               AND st_line_move.state = 'posted'
               AND st_line_move.company_id IN %s
          GROUP BY st_line_move.journal_id
        """, [tuple(bank_cash_journals.ids), tuple(self.env.companies.ids)])
        number_to_reconcile = {
            journal_id: count
            for journal_id, count in self.env.cr.fetchall()
        }

        # Last statement
        bank_cash_journals.last_statement_id.mapped(lambda s: s.balance_end_real)  # prefetch

        outstanding_pay_account_balances = bank_cash_journals._get_journal_dashboard_outstanding_payments()

        # Misc Entries (journal items in the default_account not linked to bank.statement.line)
        misc_domain = []
        for journal in bank_cash_journals:
            date_limit = journal.last_statement_id.date or journal.company_id.fiscalyear_lock_date
            misc_domain.append(
                [('account_id', '=', journal.default_account_id.id), ('date', '>', date_limit)]
                if date_limit else
                [('account_id', '=', journal.default_account_id.id)]
            )
        misc_domain = [

            ('parent_state', '=', 'posted'),
        ] + expression.OR(misc_domain)

        misc_totals = {
            account: (balance, count)
            for account, balance, count in self.env['account.move.line']._read_group(
                domain=misc_domain,
                aggregates=['balance:sum', 'id:count'],
                groupby=['account_id'])
        }

        # To check
        to_check = {
            journal: (amount, count)
            for journal, amount, count in self.env['account.bank.statement.line']._read_group(
                domain=[
                    ('journal_id', 'in', bank_cash_journals.ids),
                    ('move_id.to_check', '=', True),
                    ('move_id.state', '=', 'posted'),
                ],
                groupby=['journal_id'],
                aggregates=['amount:sum', '__count'],
            )
        }

        for journal in bank_cash_journals:
            # User may have read access on the journal but not on the company
            currency = journal.currency_id or self.env['res.currency'].browse(journal.company_id.sudo().currency_id.id)
            has_outstanding, outstanding_pay_account_balance = outstanding_pay_account_balances[journal.id]
            to_check_balance, number_to_check = to_check.get(journal, (0, 0))
            misc_balance, number_misc = misc_totals.get(journal.default_account_id, (0, 0))
            c=self.env['res.currency'].browse(journal.company_id.sudo().currency_id.id) or journal.currency_id
            # self.env['res.company'].search([('id', '=', journal.company_id.id)]).currency_id or journal.currency_id

            dashboard_data[journal.id].update({
                'number_to_check': number_to_check,
                'to_check_balance': currency.symbol + '  ' + self.format_value(to_check_balance),
                'number_to_reconcile': number_to_reconcile.get(journal.id, 0),
                'account_balance': currency.symbol + '  ' + self.format_value(journal.current_statement_balance),
                'has_at_least_one_statement': bool(journal.last_statement_id),
                'nb_lines_bank_account_balance': bool(journal.has_statement_lines),
                'outstanding_pay_account_balance': currency.symbol +'  '+ self.format_value(outstanding_pay_account_balance),
                'nb_lines_outstanding_pay_account_balance': has_outstanding,
                'last_balance': currency.symbol + '  ' + self.format_value(journal.last_statement_id.balance_end_real),
                'last_statement_id': journal.last_statement_id.id,
                'bank_statements_source': journal.bank_statements_source,
                'is_sample_data': journal.has_statement_lines,
                'nb_misc_operations': number_misc,
                'misc_operations_balance': c.symbol + '  ' + self.format_value(misc_balance),
                #   if (self.format_value(misc_balance) != self.format_value(journal.last_statement_id.balance_end_real)) else None,
            })



    def _fill_sale_purchase_dashboard_data(self, dashboard_data):
        """Populate all sale and purchase journal's data dict with relevant information for the kanban card."""
        sale_purchase_journals = self.filtered(lambda journal: journal.type in ('sale', 'purchase'))
        purchase_journals = self.filtered(lambda journal: journal.type == 'purchase')
        sale_journals = self.filtered(lambda journal: journal.type == 'sale')
        if not sale_purchase_journals:
            return
        bills_field_list = [
            "account_move.journal_id",
            "(CASE WHEN account_move.move_type IN ('out_refund', 'in_refund') THEN -1 ELSE 1 END) * account_move.amount_residual AS amount_total",
            "(CASE WHEN account_move.move_type IN ('in_invoice', 'in_refund', 'in_receipt') THEN -1 ELSE 1 END) * account_move.amount_residual_signed AS amount_total_company",
            "account_move.currency_id AS currency",
            "account_move.move_type",
            "account_move.invoice_date",
            "account_move.company_id",
        ]
        payment_field_list = [
            "account_move_line.journal_id",
            "account_move_line.move_id",
            "-account_move_line.amount_residual AS amount_total_company",
            "-account_move_line.amount_residual_currency AS amount_total",
            "account_move_line.currency_id AS currency",
        ]
        # DRAFTS
        query, params = sale_purchase_journals._get_draft_bills_query().select(*bills_field_list)
        self.env.cr.execute(query, params)
        query_results_drafts = group_by_journal(self.env.cr.dictfetchall())

        # WAITING BILLS AND PAYMENTS
        query_results_to_pay = {}
        if purchase_journals:
            query, params = purchase_journals._get_open_payments_query().select(*payment_field_list)
            self.env.cr.execute(query, params)
            query_results_payments_to_pay = group_by_journal(self.env.cr.dictfetchall())
            for journal in purchase_journals:
                query_results_to_pay[journal.id] = query_results_payments_to_pay[journal.id]
        if sale_journals:
            query, params = sale_journals._get_open_bills_to_pay_query().select(*bills_field_list)
            self.env.cr.execute(query, params)
            query_results_bills_to_pay = group_by_journal(self.env.cr.dictfetchall())
            for journal in sale_journals:
                query_results_to_pay[journal.id] = query_results_bills_to_pay[journal.id]

        # LATE BILLS AND PAYMENTS
        late_query_results = {}
        if purchase_journals:
            query, params = purchase_journals._get_late_payment_query().select(*payment_field_list)
            self.env.cr.execute(query, params)
            late_payments_query_results = group_by_journal(self.env.cr.dictfetchall())
            for journal in purchase_journals:
                late_query_results[journal.id] = late_payments_query_results[journal.id]
        if sale_journals:
            query, params = sale_journals._get_late_bills_query().select(*bills_field_list)
            self.env.cr.execute(query, params)
            late_bills_query_results = group_by_journal(self.env.cr.dictfetchall())
            for journal in sale_journals:
                late_query_results[journal.id] = late_bills_query_results[journal.id]

        to_check_vals = {
            journal.id: (amount_total_signed_sum, count)
            for journal, amount_total_signed_sum, count in self.env['account.move']._read_group(
                domain=[
                    *self.env['account.move']._check_company_domain(self.env.companies),
                    ('journal_id', 'in', sale_purchase_journals.ids),
                    ('to_check', '=', True),
                ],
                groupby=['journal_id'],
                aggregates=['amount_total_signed:sum', '__count'],
            )
        }

        self.env.cr.execute(SQL("""
            SELECT id, moves_exists
            FROM account_journal journal
            LEFT JOIN LATERAL (
                SELECT EXISTS(SELECT 1
                              FROM account_move move
                              WHERE move.journal_id = journal.id
                              AND move.company_id = ANY (%(companies_ids)s) AND
                                  move.journal_id = ANY (%(journal_ids)s)) AS moves_exists
            ) moves ON TRUE
            WHERE journal.id = ANY (%(journal_ids)s);
        """,
            journal_ids=sale_purchase_journals.ids,
            companies_ids=self.env.companies.ids,
        ))
        is_sample_data_by_journal_id = {row[0]: not row[1] for row in self.env.cr.fetchall()}

        for journal in sale_purchase_journals:
            # User may have read access on the journal but not on the company
            currency = journal.currency_id or self.env['res.currency'].browse(journal.company_id.sudo().currency_id.id)
            (number_waiting, sum_waiting) = self._count_results_and_sum_amounts(query_results_to_pay[journal.id], currency)
            (number_draft, sum_draft) = self._count_results_and_sum_amounts(query_results_drafts[journal.id], currency)
            (number_late, sum_late) = self._count_results_and_sum_amounts(late_query_results[journal.id], currency)
            amount_total_signed_sum, count = to_check_vals.get(journal.id, (0, 0))
            dashboard_data[journal.id].update({
                'number_to_check': count,
                'to_check_balance':  currency.symbol +  '  ' + self.format_value(amount_total_signed_sum),
                'title': _('Bills to pay') if journal.type == 'purchase' else _('Invoices owed to you'),
                'number_draft': number_draft,
                'number_waiting': number_waiting,
                'number_late': number_late,
                'sum_draft': currency.symbol + '  ' + self.format_value(sum_draft),
                'sum_waiting': currency.symbol + '  ' +  self.format_value(sum_waiting),
                'sum_late': currency.symbol + '  ' + self.format_value(sum_late),
                'has_sequence_holes': journal.has_sequence_holes,
                'is_sample_data': is_sample_data_by_journal_id[journal.id],
                # 'entries_count' is kept here to maintain compatibility with a view for the stable version.
                # The name will be changed in master
                'entries_count': not is_sample_data_by_journal_id[journal.id],
            })

    def _fill_general_dashboard_data(self, dashboard_data):
        """Populate all miscelaneous journal's data dict with relevant information for the kanban card."""
        general_journals = self.filtered(lambda journal: journal.type == 'general')
        if not general_journals:
            return
        to_check_vals = {
            journal.id: (amount_total_signed_sum, count)
            for journal, amount_total_signed_sum, count in self.env['account.move']._read_group(
                domain=[
                    *self.env['account.move']._check_company_domain(self.env.companies),
                    ('journal_id', 'in', general_journals.ids),
                    ('to_check', '=', True),
                ],
                groupby=['journal_id'],
                aggregates=['amount_total_signed:sum', '__count'],
            )
        }
        for journal in general_journals:
            currency = journal.currency_id or self.env['res.currency'].browse(journal.company_id.sudo().currency_id.id)
            amount_total_signed_sum, count = to_check_vals.get(journal.id, (0, 0))
            dashboard_data[journal.id].update({
                'number_to_check': count,
                'to_check_balance': currency.symbol +  '  ' + self.format_value(amount_total_signed_sum),
            })
    @api.model
    def format_value(self, value, currency=False):
        digits = (currency or self.env.company.currency_id).decimal_places
        currency = None
        value = abs(value)
        
        remain = value - math.trunc(value)
        if math.trunc(remain*10*digits) == 0:
            formatted_amount = formatLang(self.env, value, currency_obj=currency, digits=0)

        elif remain*10*digits > 0 and (remain*10*digits)%10 > 0:
            formatted_amount = formatLang(self.env, value, currency_obj=currency, digits=digits)
        else:
            formatted_amount = formatLang(self.env, value, currency_obj=currency, digits=digits-1)
        return formatted_amount