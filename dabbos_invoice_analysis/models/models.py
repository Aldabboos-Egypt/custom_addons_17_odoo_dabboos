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


class AccountInvoiceReport(models.Model):
    _inherit = 'account.invoice.report'

    product_tag_ids = fields.Many2many(
        comodel_name='product.tag',
        string="Product Template Tags",
        help="Tags associated with the product."
    )

    # def _select(self):
    #     # Extend the _select query to join the product tags
    #     select_str = super()._select()
    #     select_str += """
    #         , ARRAY_AGG(ptt.id) AS product_tag_ids
    #     """
    #     return select_str
    #
    # def _from(self):
    #     # Extend the _from query to include product tags
    #     from_str = super()._from()
    #     from_str += """
    #         LEFT JOIN product_template_product_tag_rel pt_rel ON pt_rel.product_template_id = template.id
    #         LEFT JOIN product_tag ptt ON ptt.id = pt_rel.product_tag_id
    #     """
    #     return from_str
    #
    # def _group_by(self):
    #     # Extend the _group_by query to aggregate product tags
    #     group_by_str = super()._group_by()
    #     group_by_str += ", pt_rel.product_template_id"
    #     return group_by_str
