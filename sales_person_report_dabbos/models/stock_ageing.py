
# -*- coding: utf-8 -*-
from odoo.tools import pycompat, DEFAULT_SERVER_DATETIME_FORMAT,DEFAULT_SERVER_DATE_FORMAT

from datetime import datetime, timedelta
from odoo import _, api, fields, models


class SalesPartner(models.Model):
    _name = 'sales.partner'
    name = fields.Char('name' )
    date_to = fields.Date('Date To', )
    partner_ids = fields.Many2many(comodel_name='res.partner', string="Partner",  )
    category_ids = fields.Many2many(comodel_name='res.partner.category', string="Tags",  )
    sales_partner_line_ids= fields.One2many(comodel_name='sales.partner.line',inverse_name='sales_partner_id', string='Lines',)






    @api.model
    def create(self, values):
        res = super(SalesPartner, self).create(values)
        name = str(fields.Date.today())
        res.name = name
        return res


    def clear(self):
        cr = self.env.cr
        cr.execute("delete from sales_partner_line where sales_partner_id=%s" % self.id)


    def _get_last_payment(self,partner ):
        if  self.date_to:
            move_line=self.env['account.move.line'].search(['&','&', '&', '&',('move_id.state', '=','posted'), ('journal_id.type','in',('bank','cash')), ('account_id.account_type','=','asset_receivable'), ('date','<=',self.date_to),('partner_id','=',partner.id)] )
        else:
            move_line=self.env['account.move.line'].search([ '&', '&','&',('move_id.state', '=','posted'),('journal_id.type','in',('bank','cash')),('account_id.account_type', '=', 'asset_receivable'),('partner_id','=',partner.id)  ]  )
        print("Last Payment :::",move_line)
        return move_line


    def _get_last_invoice(self,partner ):
        if  self.date_to:
            invoice_id=self.env['account.move'].search(['&','&', '&',('state', '=','posted'),('partner_id','=',partner.id),('move_type','=','out_invoice'),('date','<=',self.date_to)],order="id desc", limit=1)
        else:
            invoice_id=self.env['account.move'].search([ '&','&',('state', '=','posted'), ('partner_id','=',partner.id),('move_type','=','out_invoice') ],order="id desc", limit=1)
        print("Last Invoice :::",invoice_id)
        return invoice_id

    def compute(self):
        self.clear()
        cr = self.env.cr
        counter=1
        partners=self.env['res.partner'].search([('category_id','in',self.category_ids.ids)])
        print("pa",partners)
        print(self.partner_ids)
        partners+=self.partner_ids
        print("pa2",partners)
        for partner in partners:
            payment_date=self._get_last_payment(partner=partner)[0].date if self._get_last_payment(partner=partner) else None
            invoice_date=self._get_last_invoice(partner=partner).date if self._get_last_invoice(partner=partner) else None
            if self.date_to:
                domain = ['&','&','&',('move_id.state', '=','posted'),('partner_id', '=', partner.id), ('account_id.account_type', '=', 'asset_receivable'),('date', '<=', self.date_to)]
            else:
                domain = ['&','&',('move_id.state', '=','posted'),('partner_id', '=', partner.id) ,('account_id.account_type', '=', 'asset_receivable')]

            move_lines = self.env['account.move.line'].search(domain)
            balance = 0
            for line in move_lines:
                balance += (line.debit - line.credit)
            total_payment=0.0
            if payment_date:
                total_payment=sum(line.credit for line in self._get_last_payment(partner=partner) if line.date==payment_date)


            cr.execute(
                '''INSERT INTO sales_partner_line (sequence, partner_id,debit,credit,balance,last_invoice_amount,last_invoice_date,last_payment_amount,last_payment_date,phone,address,area,sales_partner_id) VALUES (%s,%s, %s, %s,%s, %s, %s,%s, %s, %s,%s, %s, %s)''',
                (counter,partner.id,partner.debit,partner.credit,balance,self._get_last_invoice(partner=partner).amount_total,invoice_date
                 ,total_payment,payment_date,partner.phone if partner.phone else ' ' ,partner.contact_address if partner.contact_address else '' ,partner.ref if partner.ref else '',self.id
                 ))
            counter=counter+1







        #



    def action_view_report_lines(self):
        domain = [("id", "in", self.sales_partner_line_ids.ids)]
        xmlid = "sales_person_report_dabbos.action_sales_partner_lines"
        action = self.env["ir.actions.act_window"]._for_xml_id(xmlid)
        action['domain'] = domain
        return action





class salespartnerLine(models.Model):
    _name = 'sales.partner.line'
    _rec_name = 'name'

    name=fields.Char(related="sales_partner_id.name",store=True)
    sequence = fields.Integer(string='Seq')
    partner_id= fields.Many2one(comodel_name='res.partner',string='Partner',)
    credit = fields.Float(string='Credit')
    debit = fields.Float(string='Debit')
    balance= fields.Float(string='Balance', )
    last_invoice_amount = fields.Float( string='Last Invoice Amount')
    last_invoice_date = fields.Date(string='Last Invoice Date')
    last_payment_amount = fields.Float( string='Last Payment Amount')
    last_payment_date = fields.Date(string='Last Payment Date')
    phone = fields.Char(string='Phone')
    address = fields.Char(string='Address')
    area = fields.Char(string='Area')
    notes = fields.Char(string='Notes')

    tags = fields.Char(string='Tags',compute="_compute_tags"  )

    def _compute_tags(self):
        for rec in self:
            rec.tags=''
            if rec.partner_id:
                for l in rec.partner_id.category_id:
                    rec.tags+=l.name +" - "



    sales_partner_id= fields.Many2one( comodel_name='sales.partner',string='sales partner')



