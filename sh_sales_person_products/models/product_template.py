# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

from odoo import models, fields, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    sales_persons_ids = fields.Many2many(
        "res.users",
        string="Allocate Sales Persons",
        domain="[('id', 'in', eligible_sales_person_ids)]",
    )

    eligible_sales_person_ids = fields.Many2many(
        "res.users",
        string="Eligible Sales Persons",
        compute="_compute_eligible_sales_persons",
        store=False,  # Computed field does not need to be stored unless necessary
    )

    @api.depends('company_id')
    def _compute_eligible_sales_persons(self):
        for partner in self:
            if partner.company_id:
<<<<<<< Updated upstream
                partner.eligible_sales_person_ids = self.env['res.users'].search([('company_id', '=', partner.company_id.id)])
=======
                partner.eligible_sales_person_ids = self.env['res.users'].search([('company_ids', 'in', partner.company_id.id)])
>>>>>>> Stashed changes
            else:
                partner.eligible_sales_person_ids = self.env['res.users'].search([])


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
