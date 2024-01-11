# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

from odoo import models, fields, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    sales_persons_ids = fields.Many2many(
        "res.users", string="Allocate Sales Persons")

    # To apply domain to action
    @api.model
    def default_get(self, fields):
        vals = super(ProductTemplate, self).default_get(fields)
        if self.env.user:
            vals.update({"sales_persons_ids": [(6, 0, [self.env.user.id])]})
        return vals

    def _name_search(self, name, domain=None, operator="ilike", limit=None, order=None):
        if self.env.user.has_group("sales_team.group_sale_salesman") and not (self.env.user.has_group("sales_team.group_sale_salesman_all_leads")):
            if domain is None:
                domain = []
            domain += [("sales_persons_ids", "in", self.env.user.id)]
        return super()._name_search(name, domain=domain, operator=operator, limit=limit, order=order)

    # To apply domain to load menu _________ 1
    @api.model
    @api.returns('self')
    def search_fetch(self, domain, field_names, offset=0, limit=None, order=None):
        if self.env.user.has_group("sales_team.group_sale_salesman") and not (self.env.user.has_group("sales_team.group_sale_salesman_all_leads")):
            domain += [("sales_persons_ids", "in", self.env.user.id)]

        return super().search_fetch(domain, field_names, offset, limit, order)
