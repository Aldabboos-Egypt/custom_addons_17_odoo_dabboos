'''
Created on Jan 29, 2019

@author: Zuhair Hammadi
'''
from odoo import models, fields, api

class PurchaseOrder(models.Model):
    _inherit = "purchase.order"
    
    company_currency_id = fields.Many2one('res.currency', related='company_id.currency_id', string="Company Currency", readonly=True)
    
    amount_untaxed_company = fields.Monetary(string='Untaxed Amount in Company Currency', store=True, readonly=True, compute='_amount_all', currency_field='company_currency_id')
    amount_tax_company = fields.Monetary(string='Taxes in Company Currency', store=True, readonly=True, compute='_amount_all', currency_field='company_currency_id')
    amount_total_company = fields.Monetary(string='Total in Company Currency', store=True, readonly=True, compute='_amount_all', currency_field='company_currency_id')    
    
    other_currency = fields.Boolean(compute = '_calc_other_currency')
    
    @api.depends('currency_id', 'company_currency_id')
    def _calc_other_currency(self):
        for record in self:
            record.other_currency = record.currency_id != record.company_currency_id
    
    @api.depends('order_line.price_total', 'company_id','date_order', 'currency_id')
    def _amount_all(self):    
        super(PurchaseOrder, self)._amount_all()
        for order in self:
            for fname in ['amount_untaxed', 'amount_tax', 'amount_total']:
                order[fname + '_company'] = order.currency_id._convert(order[fname], order.company_currency_id, order.company_id, order.date_order)
