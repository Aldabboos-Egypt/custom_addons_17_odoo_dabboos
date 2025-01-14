from odoo import fields, models,api




class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    salesperson_id = fields.Many2one(
        'res.users',
        string='Salesperson',
        related='move_id.invoice_user_id',
        store=True
    )
    product_tag_ids = fields.Many2many(
        'product.tag',
        string='Product Tags',
        compute='_compute_product_tags',
        store=True
    )


    @api.depends('product_id')
    def _compute_product_tags(self):
        for line in self:
            line.product_tag_ids = line.product_id.product_tag_ids.ids if line.product_id else False


 