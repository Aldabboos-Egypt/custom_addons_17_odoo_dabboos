# Part of odoo. See LICENSE file for full copyright and licensing details.
import folium
import os
from odoo import api, models, fields,SUPERUSER_ID
from odoo import api, fields, models,_
from odoo.exceptions import ValidationError
from odoo import models, fields, api
from datetime import datetime, timedelta
import math

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

    is_salesperson = fields.Boolean(string='',)


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

    is_salesperson = fields.Boolean(string='',)


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

    def write(self, vals):
        res = super(ResUsers, self).write(vals)
        if 'is_salesperson' in vals:
            for record in self:
                record.partner_id.write({'is_salesperson': vals['is_salesperson']})
        return res

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


class SalespersonLocation(models.Model):
    _name = 'salesperson.location'
    _description = 'Salesperson Location'
    _rec_name = 'salesperson_id'

    salesperson_id = fields.Many2one('res.users', string="Salesperson", required=True)
    partner_id = fields.Many2one('res.partner',related="salesperson_id.partner_id" )
    customer_id = fields.Many2one('res.partner', string="Customer", help="Customer associated with this location")
    latitude = fields.Float(string="Latitude", required=True)
    longitude = fields.Float(string="Longitude", required=True)
    timestamp = fields.Datetime(string="Timestamp", default=fields.Datetime.now, required=True)
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)

    # New fields
    device_id = fields.Char(string="Device ID")
    os = fields.Char(string="Operating System")
    app_version = fields.Char(string="App Version")
    map_link = fields.Char(string="Location Link", compute="_compute_map_link", store=True)
    distance_from_last = fields.Float(string="Distance from Last (km)", compute="_compute_distance", store=True)

    @api.depends('latitude', 'longitude')
    def _compute_map_link(self):
        for record in self:
            if record.latitude and record.longitude:
                record.map_link = (
                    f"https://www.google.com/maps/place/@{record.latitude},{record.longitude},18z/"
                )
            else:
                record.map_link = ""

    @api.depends('latitude', 'longitude', 'salesperson_id')
    def _compute_distance(self):
        for record in self:
            if not record.id:  # Skip computation if record is not yet saved
                record.distance_from_last = 0.0
                continue

            last_location = self.env['salesperson.location'].search([
                ('salesperson_id', '=', record.salesperson_id.id),
                ('id', '<', record.id)
            ], order="timestamp desc", limit=1)

            if last_location:
                record.distance_from_last = self._haversine_distance(
                    last_location.latitude, last_location.longitude,
                    record.latitude, record.longitude
                )
            else:
                record.distance_from_last = 0.0

    @staticmethod
    def _haversine_distance(lat1, lon1, lat2, lon2):
        """Calculate the Haversine distance (in km) between two latitude-longitude points."""
        R = 6371  # Radius of Earth in km
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat/2) * math.sin(dlat/2) + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2) * math.sin(dlon/2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        return R * c

    @api.model
    def cleanup_old_records(self):
        """Delete records older than 30 days."""
        cutoff_date = datetime.now() - timedelta(days=30)
        self.search([('timestamp', '<', cutoff_date)]).unlink()

    def action_open_map(self):
        """ Open the movement map wizard """
        return {
            'type': 'ir.actions.act_window',
            'name': 'Salesperson Map',
            'view_mode': 'form',
            'res_model': 'salesperson.location.map.wizard',
            'target': 'new',  # Opens as a dialog
            'context': {'default_salesperson_id': self.salesperson_id.id},
        }




class ResPartner(models.Model):
    _inherit = 'res.partner'

    salesperson_locations = fields.One2many(
        'salesperson.location', 'partner_id', string="Salesperson Locations"
    )

    customer_locations = fields.One2many(
        'salesperson.location', 'customer_id', string="Customer Locations"
    )


class SalespersonLocationMapWizard(models.TransientModel):
    _name = 'salesperson.location.map.wizard'
    _description = 'Salesperson Location Map Wizard'

    salesperson_id = fields.Many2one('res.users', string="Salesperson", required=True)
    map_file = fields.Char(string="Map File", readonly=True)  # Store the static file URL

    def action_generate_map(self):
        """ Generate the salesperson movement map and store it as a static file """

        locations = self.env['salesperson.location'].search([
            ('salesperson_id', '=', self.salesperson_id.id)
        ], order="timestamp asc")

        if not locations:
            raise ValueError("No location data found for this salesperson.")

        # Create the map centered on the first location
        first_location = locations[0]
        folium_map = folium.Map(location=[first_location.latitude, first_location.longitude], zoom_start=12)

        # Add salesperson movement points
        coordinates = []
        for loc in locations:
            folium.Marker([loc.latitude, loc.longitude], popup=f"Time: {loc.timestamp}").add_to(folium_map)
            coordinates.append([loc.latitude, loc.longitude])

        # Draw movement path
        if len(coordinates) > 1:
            folium.PolyLine(coordinates, color="red", weight=2.5, opacity=1).add_to(folium_map)

        # Get the module static directory path
        module_path = os.path.dirname(os.path.abspath(__file__))  # Get module's absolute path
        static_folder = os.path.join(module_path, '../static/maps')  # Save in static/maps folder
        os.makedirs(static_folder, exist_ok=True)  # Create folder if not exists

        # Save map file
        file_name = f"salesperson_map_{self.salesperson_id.id}.html"
        map_file_path = os.path.join(static_folder, file_name)

        folium_map.save(map_file_path)

        # ✅ Verify file size to confirm it's not empty
        if os.path.getsize(map_file_path) == 0:
            raise ValueError("Generated map file is empty!")

        # Set the static URL
        self.map_file = f"/dabbos_restapi/static/maps/{file_name}"

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'salesperson.location.map.wizard',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
        }
