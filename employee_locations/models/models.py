from odoo import models, fields,api

class EmployeeLocation(models.Model):
    _name = 'employee.location'
    _description = 'Employee Location'

    employee_id = fields.Many2one('hr.employee', string='Employee', required=True, ondelete='cascade')
    latitude = fields.Float(string='Latitude', required=True)
    longitude = fields.Float(string='Longitude', required=True)
    check_in_allowed = fields.Float(string='Check In Allowed', required=True)

class Employee(models.Model):
    _inherit = 'hr.employee'

    location_ids = fields.One2many(
        'employee.location', 'employee_id', string='Locations'
    )

    @api.model
    def get_allowed_locations(self, employee_id):
        """
        Get all allowed locations for the given employee ID.

        :param int employee_id: The ID of the employee.
        :return: A list of dictionaries containing allowed locations with latitude and longitude.
        :rtype: list
        """
        # Search for the employee
        employee = self.env['hr.employee'].browse(employee_id)

        # Ensure the employee exists
        if not employee:
            return []

        # Filter allowed locations
        allowed_locations = employee.location_ids.filtered(lambda loc: loc.check_in_allowed)

        # Convert to a list of dictionaries
        location_list = [{
            'latitude': loc.latitude,
            'longitude': loc.longitude,
        } for loc in allowed_locations]

        return location_list
