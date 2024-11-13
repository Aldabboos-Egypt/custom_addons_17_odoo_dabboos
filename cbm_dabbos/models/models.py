# models.py

from odoo import models, fields, api

class Product(models.Model):
    _inherit = 'product.template'

    length = fields.Float(string='Length', readonly=False)
    width = fields.Float(string='Width', readonly=False)
    height = fields.Float(string='Height', readonly=False)
    cbm = fields.Float(string='cbm', compute='_compute_cbm', store=True, readonly=True)

    @api.depends('length', 'width', 'height')
    def _compute_cbm(self):
        for product in self:
            product.cbm = product.length * product.width * product.height

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    length = fields.Float(string='Length',  )
    width = fields.Float(string='Width', )
    height = fields.Float(string='Height', )
    cbm = fields.Float(string='cbm', compute='_compute_cbm', store=True, readonly=True)

    @api.onchange('product_id')
    def product_changed(self):
        if self.product_id:
            self.length=self.product_id.length
            self.width=self.product_id.width
            self.height=self.product_id.height

    @api.onchange('length','width','height')
    def attrs_changed(self):
            self.product_id.length=self.length
            self.product_id.width=self.width
            self.product_id.height=self.height


    @api.depends('length', 'width', 'height')
    def _compute_cbm(self):
        for product in self:
            product.cbm = product.length * product.width * product.height

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'


    length = fields.Float(string='Length',  )
    width = fields.Float(string='Width', )
    height = fields.Float(string='Height', )
    cbm = fields.Float(string='cbm', compute='_compute_cbm', store=True, readonly=True)

    @api.onchange('product_id')
    def product_changed(self):
        if self.product_id:
            self.length=self.product_id.length
            self.width=self.product_id.width
            self.height=self.product_id.height

    @api.onchange('length','width','height')
    def attrs_changed(self):
            self.product_id.length=self.length
            self.product_id.width=self.width
            self.product_id.height=self.height


    @api.depends('length', 'width', 'height')
    def _compute_cbm(self):
        for product in self:
            product.cbm = product.length * product.width * product.height

class AccountInvoiceLine(models.Model):
    _inherit = 'account.move.line'

    length = fields.Float(string='Length',  )
    width = fields.Float(string='Width', )
    height = fields.Float(string='Height', )
    cbm = fields.Float(string='cbm', compute='_compute_cbm', store=True, readonly=True)

    @api.onchange('product_id')
    def product_changed(self):
        if self.product_id:
            self.length=self.product_id.length
            self.width=self.product_id.width
            self.height=self.product_id.height

    @api.onchange('length','width','height')
    def attrs_changed(self):
            self.product_id.length=self.length
            self.product_id.width=self.width
            self.product_id.height=self.height


    @api.depends('length', 'width', 'height')
    def _compute_cbm(self):
        for product in self:
            product.cbm = product.length * product.width * product.height
