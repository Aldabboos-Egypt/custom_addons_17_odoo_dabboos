# Part of odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, models, fields,SUPERUSER_ID

from odoo import api, fields, models


class IrModel(models.Model):
    _inherit = "ir.model"
    rest_api = fields.Boolean("REST API",  help="Allow this model to be fetched through REST API")




class FetchData(models.Model):
    _name = 'fetch.data'
    _rec_name="model_id"

    model_id = fields.Many2one(
        comodel_name='ir.model',
        string='Model',
        ondelete='cascade',
        required=True,
        domain=[('transient', '=', False)],
    )
    field_ids= fields.Many2many(comodel_name='ir.model.fields',required=True, string='Fields', domain="[('model_id','=',model_id)]")



class Partner(models.Model):
    _inherit = "res.partner"

    area = fields.Char(string='Area')
    state = fields.Char(string='State')
    description = fields.Text(string='Description')
    lat = fields.Char(string='Latitude')
    lang = fields.Char(string='Longitude')
    date = fields.Date(string='Date')


    def create_partner(self, vals):
        with self.pool.cursor() as cr:
            res = self.with_env(self.env(cr=cr, user=SUPERUSER_ID)).create(vals)
            return res

    def update_partner(self, vals):
        with self.pool.cursor() as cr:
            res = self.with_env(self.env(cr=cr, user=SUPERUSER_ID)).write(vals)
            return res


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    api_payment = fields.Boolean(string='API Payment')

class AccountPaymentMethod(models.Model):
    _inherit = 'account.payment.method'

    api_payment = fields.Boolean(string='API Payment')



class SaleOrder(models.Model):
    _inherit = 'sale.order'

    extra_notes= fields.Char(
        string='Notes',
        required=False)

    def create_order(self, vals):
        with self.pool.cursor() as cr:
            res = self.with_env(self.env(cr=cr, user=SUPERUSER_ID)).create(vals)
            return res

    def update_order(self, vals):
        with self.pool.cursor() as cr:
            res = self.with_env(self.env(cr=cr, user=SUPERUSER_ID)).write(vals)
            return res

    def get_name(self):
        with self.pool.cursor() as cr:
            res = self.with_env(self.env(cr=cr, user=SUPERUSER_ID)).name
            return res



    total_product_api = fields.Integer(string='Total Product Api :',compute='_total_product',help="total Products",store=True,readonly=True)
    total_quantity_api = fields.Integer(string='Total Quantity Api :',compute='_total_quantity',help="total Quantity",store=True,readonly=True)


    def _total_product(self):
        for record in self:
            record.total_product_api = len(record.order_line)

    def _total_quantity(self):
        for record in self:
            total_qty = 0
            for line in record.order_line:
                total_qty = total_qty + line.product_uom_qty
            record.total_quantity_api = total_qty

class AccountMove(models.Model):
    _inherit = 'account.move'

    def create_invoice(self, vals):
        with self.pool.cursor() as cr:
            res = self.with_env(self.env(cr=cr, user=SUPERUSER_ID)).create(vals)
            return res

    def update_invoice(self, vals):
        with self.pool.cursor() as cr:
            res = self.with_env(self.env(cr=cr, user=SUPERUSER_ID)).write(vals)
            return res




class ResUsers(models.Model):
    _inherit = 'res.users'

    allowed_locations = fields.Many2many(
        comodel_name='stock.location',
        string='Allowed Locations')

    def _get_qty(self):
        with self.pool.cursor() as cr:
            location_ids = self.with_env(self.env(cr=cr, user=SUPERUSER_ID)).allowed_locations
            print(location_ids.ids)

            quants = self.env['stock.quant'].search([
                ('location_id', 'in', location_ids.ids),
            ])

            # Create a dictionary to store product quantities
            quantities = {}

            # Iterate through quants and update the quantities dictionary
            for quant in quants:
                print(quant)
                if quant.product_id.id not in quantities:
                    quantities[quant.product_id.id] = quant.quantity
                else:
                    quantities[quant.product_id.id] += quant.quantity

            return quantities


class SaleOrderLineInherit(models.Model):
    _inherit = 'sale.order.line'

    sale_order_note = fields.Char("Notes")