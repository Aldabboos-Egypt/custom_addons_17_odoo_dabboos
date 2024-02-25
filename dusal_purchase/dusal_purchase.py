# models/purchase.py

from odoo import api, fields, models

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    print_product_image = fields.Boolean(
        string='Print product image', readonly=False,
        help="If this checkbox checked then print product images on Purchase order & RFQ", default=True)
    image_size = fields.Selection(
        [('small', 'Small'), ('medium', 'Medium'), ('big', 'Big')],
        string='Image sizes', help="Choose an image size here", default='small')
    print_line_number = fields.Boolean(
        string='Print line number', readonly=False,
        help="Print line number on Purchase order & RFQ", default=False)


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    product_image = fields.Binary(string="Image", related="product_id.image_1024")
    product_image_medium = fields.Binary(string="Image medium", related="product_id.image_256")
    product_image_small = fields.Binary(string="Image small", related="product_id.image_128")
