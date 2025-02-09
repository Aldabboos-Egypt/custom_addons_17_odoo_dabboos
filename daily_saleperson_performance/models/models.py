
# -*- coding: utf-8 -*-
from odoo.tools import pycompat, DEFAULT_SERVER_DATETIME_FORMAT,DEFAULT_SERVER_DATE_FORMAT

from datetime import datetime, timedelta
from odoo import _, api, fields, models


class Salesdues(models.Model):
    _name = 'sales.dues'
    name = fields.Char('name' )
    date_from = fields.Date('Date From',required=True )
    date_to = fields.Date('Date To',required=True )
    user_ids = fields.Many2many(comodel_name='res.users', string="Sales Person",  )
    sales_dues_line_ids= fields.One2many(comodel_name='sales.dues.line',inverse_name='sales_dues_id', string='Lines',)






    @api.model
    def create(self, values):
        res = super(Salesdues, self).create(values)
        name = str(fields.Date.today())
        res.name = name
        return res


    def clear(self):
        cr = self.env.cr
        cr.execute("delete from sales_dues_line where sales_dues_id=%s" % self.id)




    def _get_invoice_ids(self,user ):
        if  self.date_to and self.date_from:
            invoice_ids=self.env['account.move'].search(['&','&', '&','&',('state', '=','posted'),('partner_id.user_id','=',user.id),('move_type','=','out_invoice'),('date','>=',self.date_from),('date','<=',self.date_to)] )
        else:
            invoice_ids=self.env['account.move'].search([ '&','&',('state', '=','posted'), ('partner_id.user_id','=',user.id),('move_type','=','out_invoice') ] )
        # print(invoice_ids)
        return invoice_ids

    def compute(self):
        self=self.sudo()
        self.clear()
        cr = self.env.cr
        counter=1
        for user in self.user_ids:
            today_invoice_ids=self._get_invoice_ids(user=user).filtered(lambda invoice: invoice.invoice_date ==self.date_to)
            number_of_invoices=len(self._get_invoice_ids(user=user).filtered(lambda invoice: invoice.invoice_date ==self.date_to))
            invoice_value_daily= sum(invoice.amount_total_signed for invoice in today_invoice_ids )

            total_sales= sum(invoice.amount_total_signed for invoice in self._get_invoice_ids(user=user))

            if self.date_to and self.date_from:

                domain = ['&', '&', '&',  '&','&', ('move_id.state', '=', 'posted'), ('partner_id.user_id', '=', user.id),
                          ('account_id.account_type', '=', 'asset_receivable'),  ('journal_id.type', 'in',('cash','bank')), ('date', '>=', self.date_from), ('date', '<=', self.date_to)]
            else:
                domain = ['&', '&','&', ('move_id.state', '=', 'posted'), ('partner_id.user_id', '=', user.id),
                          ('journal_id.type', 'in', ('cash', 'bank')),
                          ('account_id.account_type', '=', 'asset_receivable')]

            move_lines =  self.env['account.move.line'].search(domain)

            move_lines_daily = move_lines.filtered(lambda line: line.date == self.date_to)
            total_collections = sum(line.credit for line in move_lines)
            value_collections_daily = sum(line.credit for line in move_lines_daily)


            move_line_for_debit =  self.env['account.move.line'].search(['&','&',('account_id.account_type', '=', 'asset_receivable'),('move_id.state', '=', 'posted'),('partner_id.user_id','=',user.id)])


            print(len(move_line_for_debit))
            total_debt =sum(line.balance for line in move_line_for_debit)



            # print(number_of_invoices)
            # print(invoice_value_daily)
            # print(total_sales)
            # print(value_collections_daily)
            # print(total_collections)

            cr.execute( '''INSERT INTO sales_dues_line (sequence, user_id,number_of_invoices,invoice_value_daily,total_sales,value_collections_daily,total_collections,total_debt,sales_dues_id) VALUES (%s,%s, %s, %s,%s, %s, %s,%s,%s)''', (counter,user.id,number_of_invoices,invoice_value_daily,total_sales,value_collections_daily,total_collections,total_debt,self.id))
            counter=counter+1







        #



    def action_view_report_lines(self):
        domain = [("id", "in", self.sales_dues_line_ids.ids)]
        xmlid = "daily_saleperson_performance.action_sales_dues_lines"
        action = self.env["ir.actions.act_window"]._for_xml_id(xmlid)
        action['domain'] = domain
        return action





class salesduesLine(models.Model):
    _name = 'sales.dues.line'
    _rec_name = 'name'

    name=fields.Char(related="sales_dues_id.name",store=True)
    sequence = fields.Integer(string='Seq')
    user_id= fields.Many2one(comodel_name='res.users',string='Sales Person',)
    number_of_invoices = fields.Integer(string='Num Of Invoices')
    invoice_value_daily = fields.Float(string='Invoice value daily' )
    total_sales = fields.Float(string='Total sales')
    value_collections_daily = fields.Float(string='value collections daily')
    total_collections = fields.Float(string='Total collections')
    total_debt = fields.Float(string='total debt')



    sales_dues_id= fields.Many2one( comodel_name='sales.dues',string='sales dues')



