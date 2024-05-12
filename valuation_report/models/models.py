# -*- coding: utf-8 -*-

from odoo import models, fields, _, api
from odoo.exceptions import ValidationError

class trading_valuation(models.Model):
    _name = 'trading.valuation'
    _description = 'Trading Valuation'
    name = fields.Char(required=1)
    date_from = fields.Date(string='Date From',required=1)
    date_to = fields.Date(string='Date To',required=1)
    line_ids= fields.One2many(
        comodel_name='trading.valuation.line',
        inverse_name='trading_valuation_id',
        string='lines',
    )




    def clear(self):
        cr = self.sudo().env.cr
        cr.execute("delete from trading_valuation_line where trading_valuation_id=%s" % self.id)





    def compute(self):

        self.clear()

        cr = self.sudo().env.cr


        income_data=self.compute_vals(type='income')
        total_credit_income = total_debit_income  = 0.0

        for income_rec in income_data:
            total_debit_income = total_debit_income + income_rec.get("debit")
            total_credit_income = total_credit_income + income_rec.get("credit")

        val = (0, 0, {
            'display_type': 'line_section',
            'name': 'الايرادات',
            'credit':total_credit_income,
            'debit': total_debit_income
        })
        lines = []
        lines.append(val)
        self.update({'line_ids': lines})
        for line in income_data:
            cr.execute('''INSERT INTO trading_valuation_line (name, debit, credit,trading_valuation_id) VALUES (%s,%s, %s,%s )''',
                       (line.get('name'), line.get("debit"),line.get("credit"), self.id))



        ################################################################


        debit_valuation = self.env['stock.valuation.layer'].search(['&', ('product_id.type', '=', 'product'), ('create_date', '<=', self.date_from) ])
        credit_valuation = self.env['stock.valuation.layer'].search(['&', ('product_id.type', '=', 'product'), ('create_date', '<=', self.date_to) ])

        sum_credit_valuation =sum_debit_valuation= 0.0
        for rec in debit_valuation:
            sum_debit_valuation=sum_debit_valuation+rec.value
        for rec in credit_valuation:
            sum_credit_valuation = sum_credit_valuation + rec.value

        cost_of_revenue_data = self.compute_vals(type='cost_of_revenue')
        sum_revenue_credit = sum_revenue_debit = 0.0

        for cor_rec in cost_of_revenue_data:
            sum_revenue_debit = sum_revenue_debit + cor_rec.get("debit")
            sum_revenue_credit = sum_revenue_credit + cor_rec.get("credit")

        val = (0, 0, {
            'display_type': 'line_section',
            'name': 'تكلفة البضاعة المباعة ',
            'credit': sum_revenue_credit+sum_credit_valuation,
            'debit': sum_revenue_debit+sum_debit_valuation,

        })
        lines = []
        lines.append(val)
        self.update({'line_ids': lines})

        cr.execute( '''INSERT INTO trading_valuation_line (name, debit,trading_valuation_id) VALUES (%s,%s, %s )''',  ("رصيد  المخازن أول مدة", sum_debit_valuation,  self.id))

        cost_of_revenue_data = self.compute_vals(type='cost_of_revenue')
        for line in cost_of_revenue_data:
            cr.execute('''INSERT INTO trading_valuation_line (name, debit, credit,trading_valuation_id) VALUES (%s,%s, %s,%s )''',
                       (line.get('name'), line.get("debit"),line.get("credit"), self.id))

        cr.execute( '''INSERT INTO trading_valuation_line (name, credit,trading_valuation_id) VALUES (%s,%s, %s )''',  ("رصيد  المخازن أخر مدة ", sum_credit_valuation ,  self.id))

        ################################################################

        #
        # for line in self.line_ids:
        #     debit = debit + line.debit
        #     credit = credit + line.credit

        val = (0, 0, {
            'display_type': 'line_section',
            'name': 'مجمل الربح ',
            'credit': total_credit_income+sum_revenue_credit+sum_credit_valuation,
            'debit': total_debit_income+sum_revenue_debit+sum_debit_valuation,

        })
        lines = []
        lines.append(val)
        self.update({'line_ids': lines})



        ##########################################################################3

        expense_data=self.compute_vals()
        total_expense_credit = total_expense_debit = 0.0

        for expense_rec in expense_data:
            total_expense_debit = total_expense_debit + expense_rec.get("debit")
            total_expense_credit = total_expense_credit + expense_rec.get("credit")



        val = (0, 0, {
            'display_type': 'line_section',
            'name': 'المصاريف',
            'credit': total_expense_credit,
            'debit': total_expense_debit
        })
        lines = []
        lines.append(val)
        self.update({'line_ids': lines})
        expense_data=self.compute_vals()
        for line in expense_data:
            cr.execute('''INSERT INTO trading_valuation_line (name, debit, credit,trading_valuation_id) VALUES (%s,%s, %s,%s )''',
                       (line.get('name'), line.get("debit"),line.get("credit"), self.id))
        ##########################################################################3
        # 'credit': total_credit_income + sum_revenue_credit + sum_credit_valuation,
        # 'debit': total_debit_income + sum_revenue_debit + sum_debit_valuation,



        val = (0, 0, {
            'display_type': 'line_section',
            'name': '  صافي الربح ',
            'credit': total_credit_income + sum_revenue_credit + sum_credit_valuation+total_expense_credit,
            'debit': total_debit_income + sum_revenue_debit + sum_debit_valuation+total_expense_debit,
         })
        lines = []
        lines.append(val)
        self.update({'line_ids': lines})

    def compute_vals(self,type='expense'):
        print( self.date_from )
        # print( self.date_from.date())

        mov_line_vals = self.env['account.move.line'].search([  '&', '&', '&', ('move_id.state','=','posted'),('date', '>=', self.date_from ), ('date', '<=', self.date_to ), ('account_id.internal_group', '=', type)])
        data=[]
        accounts=mov_line_vals.mapped('account_id')
        for account in accounts:
            lines=mov_line_vals.filtered(lambda l: l.account_id.id == account.id)
            debit=credit=0
            print(account.name)
            for line in lines:
                print(line.debit)
                debit+=line.debit
                credit+=line.credit
            data.append(
                {
                    'name':account.name,
                    'debit': debit,
                    'credit': credit
                }
            )



        return data




class trading_valuation_line(models.Model):
    _name = 'trading.valuation.line'
    sequence= fields.Integer(
        string='',
        required=False)
    hide_from_report= fields.Boolean(
        string='Hide With Report',
        required=False)
    name = fields.Char('reference')
    debit= fields.Float(string='Debit')
    credit= fields.Float(string='Credit')
    balance= fields.Float(string='Balance',compute="compute_balance")
    trading_valuation_id= fields.Many2one(comodel_name='trading.valuation',string='trading valuation',)



    display_type = fields.Selection([
        ('line_section', "Section"),
        ('line_note', "Note")], default='line_note', help="Technical field for UX purpose.")

    def compute_balance(self):
        for rec in self:
            rec.balance=rec.credit-rec.debit