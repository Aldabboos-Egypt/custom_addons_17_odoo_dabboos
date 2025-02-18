# Part of odoo. See LICENSE file for full copyright and licensing details.
import json

from odoo import api, models, fields,SUPERUSER_ID
from datetime import timedelta
from odoo import api, fields, models,_
from odoo.exceptions import ValidationError

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

    visit_count = fields.Integer(string='Visits', compute='_compute_visit_count')


    def _compute_visit_count(self):
        for partner in self:
            partner.visit_count = self.env['sales.visit'].search_count([('partner_id', '=', partner.id)])

    def action_view_visits(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Visits',
            'view_mode': 'tree,form',
            'res_model': 'sales.visit',
            'domain': [('partner_id', '=', self.id)],
            'context': dict(self._context, create=False),
        }


    area = fields.Char(string='Area')
    state = fields.Char(string='State')
    description = fields.Text(string='Description')


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


    company_id = fields.Many2one(
        comodel_name='res.company',
        required=True, index=True,
        default=lambda self: self.env.user.company_id)

    notes_for_customer= fields.Char(
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

    def get_claimable_rewards_api(self):
        with self.pool.cursor() as cr:
            res = self.with_env(self.env(cr=cr, user=SUPERUSER_ID))._get_claimable_rewards()


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
        string='Allowed Locations',domain="['|',('company_id', '=',company_id),('company_id', '=',False)]",
        default=lambda self: self.env['stock.location'].search([('usage', '=', 'internal')])
    )


    allow_edit_customer_location = fields.Boolean(
        string="Allow to Edit Customer Location",
        help="Enable this option to allow the user to edit the customer location."
    )
    allow_order_outof_location = fields.Boolean(
        string="Allow to Make Order Out of Customer Location",
        help="Enable this option to allow the user to create orders outside of the customer's location."
    )
    show_qty = fields.Boolean(
        string="Show Quantity",
        help="Enable this option to allow the user to view product quantities."
    )



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




class SalesVisit(models.Model):
    _name = 'sales.visit'
    _description = 'Sales Visit'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Name')
    partner_id = fields.Many2one('res.partner', string='Partner', required=True)
    user_id = fields.Many2one('res.users', string='Sales Person', required=True, default=lambda self: self.env.user)

    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)

    from_time = fields.Datetime(string='From Time', required=True)
    to_time = fields.Datetime(string='To Time')




    notes = fields.Text(string='Notes')


    stage_id = fields.Many2one(
        'visit.stage',
        string='Stage',
        tracking=True,
        default=lambda self: self._default_stage()
    )

    @api.model
    def cron_delete_old_visit_attachments(self):
        """ Deletes attachments of visits older than 60 days """
        sixty_days_ago = fields.Datetime.now() - timedelta(days=60)
        old_visits = self.search([('create_date', '<', sixty_days_ago)])

        for visit in old_visits:
            attachments = self.env['ir.attachment'].search([
                ('res_model', '=', 'sales.visit'),
                ('res_id', '=', visit.id)
            ])
            attachments.unlink()

        return True


    def _default_stage(self):
        return self.env['visit.stage'].search([], order="sequence asc", limit=1).id

    message_ids = fields.One2many('mail.message', 'res_id', string="Messages", domain=[('model', '=', 'sales.visit')])
    message_follower_ids = fields.One2many('mail.followers', 'res_id', string="Followers",
                                           domain=[('res_model', '=', 'sales.visit')])
    attachment_ids = fields.One2many('ir.attachment', 'res_id', domain=[('res_model', '=', 'sales.visit')],
                                     string='Attachments')

    from_time_str = fields.Char(string='From Time (Str)')
    to_time_str = fields.Char(string='To Time (Str)')

    @api.model
    def create(self, vals):
        if not vals.get('name') or vals['name'] == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('visit.seq') or _('New')
        return super(SalesVisit, self).create(vals)

    duration = fields.Float(string="Duration (Hours)", compute="_compute_duration", store=True)

    @api.depends('from_time', 'to_time')
    def _compute_duration(self):
        for visit in self:
            if visit.from_time and visit.to_time:
                delta = visit.to_time - visit.from_time
                total_seconds = delta.total_seconds()
                visit.duration = total_seconds / 3600.0  # Store as hours (e.g., 2.5 for 2 hours 30 mins)
            else:
                visit.duration = 0.0


class VisitStage(models.Model):
    _name = 'visit.stage'
    _description = 'Visit Stage'

    name = fields.Char(string="Stage Name", required=True)
    sequence = fields.Integer(string="Sequence", default=1)
    is_draft = fields.Boolean(string="Draft Stage", default=False)
    is_closed = fields.Boolean(string="Closed Stage", default=False)

    @api.constrains('is_draft', 'is_closed')
    def _check_unique_draft_closed(self):
        for record in self:
            if record.is_draft:
                existing_draft = self.search_count([('is_draft', '=', True), ('id', '!=', record.id)])
                if existing_draft:
                    raise ValidationError("Only one draft stage is allowed.")

            if record.is_closed:
                existing_closed = self.search_count([('is_closed', '=', True), ('id', '!=', record.id)])
                if existing_closed:
                    raise ValidationError("Only one closed stage is allowed.")
