# -*- coding: utf-8 -*-
# Copyright (C) Softhealer Technologies.

from odoo import models, fields, api
from odoo import api, fields, models
from odoo.osv import expression



class ResPartner(models.Model):
    _inherit = "res.partner"

    sales_persons_ids = fields.Many2many(
        "res.users",
        string="Allocate Sales Persons",domain="['|',('company_id', '=',company_id),('company_id', '=',False)]",
    )

    @api.model
    def default_get(self, fields):
        vals = super(ResPartner, self).default_get(fields)

        if self.env.user and not self.env.su:
            vals.update({
                "user_id": self.env.user.id,
                "sales_persons_ids": [(6, 0, [self.env.user.id])]
            })

        return vals



    def action_sales_person_customer_update(self):
        return {
            'name':
            'Mass Update',
            'res_model':
            'sh.res.partner.mass.update.wizard',
            'view_mode':
            'form',
            'context': {
                'default_res_partner_ids':
                [(6, 0, self.env.context.get('active_ids'))]
            },
            'view_id':
            self.env.ref(
                'sh_sales_person_customer.sh_res_partner_update_wizard_form_view').
            id,
            'target':
            'new',
            'type':
            'ir.actions.act_window'
        }

    @api.model
    def _name_search(self, name, domain=None, operator='ilike', limit=None, order=None):
        """ For expense, we want to show all sales order but only their display_name (no ir.rule applied), this is the only way to do it. """
        
        # FOR SUPER USER WE DO NOTHING
        if self.env.su:
            return super()._name_search(name, domain, operator, limit, order)

        # if user 
        #   has 'User: Own Documents Only' and 
        #   not have 'User: All Documents' then we add
        #   our domain
        if (
            self.user_has_groups('sales_team.group_sale_salesman')
            and not self.user_has_groups('sales_team.group_sale_salesman_all_leads')
        ):
            list_user_ids = self.env.user.ids
            list_partner_ids = self.env.user.partner_id.ids
            domain_own_customer =  ['|','|', 
                                        ('sales_persons_ids', 'in', list_user_ids), 
                                        ('user_id', 'in', list_user_ids),
                                        ('id', 'in', list_partner_ids)
                                    ]
            domain = expression.AND([domain or [],domain_own_customer])
        return super()._name_search(name, domain, operator, limit, order)


        
    @api.model
    def web_search_read(self, domain, specification, offset=0, limit=None, order=None, count_limit=None):
        # FOR SUPER USER WE DO NOTHING
        if self.env.su:
            return super().web_search_read(domain, specification, offset=offset, limit=limit, order=order, count_limit=count_limit)

        # if user 
        #   has 'User: Own Documents Only' and 
        #   not have 'User: All Documents' then we add
        #   our domain
        if (
            self.user_has_groups('sales_team.group_sale_salesman')
            and not self.user_has_groups('sales_team.group_sale_salesman_all_leads')
        ):
            list_user_ids = self.env.user.ids
            list_partner_ids = self.env.user.partner_id.ids
            domain_own_customer =  ['|','|', 
                                        ('sales_persons_ids', 'in', list_user_ids), 
                                        ('user_id', 'in', list_user_ids),
                                        ('id', 'in', list_partner_ids)
                                    ]
            domain = expression.AND([domain or [],domain_own_customer])
        return super().web_search_read(domain, specification, offset=offset, limit=limit, order=order, count_limit=count_limit)
