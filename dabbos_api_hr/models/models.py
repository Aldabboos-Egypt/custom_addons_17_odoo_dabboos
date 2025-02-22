# -*- coding: utf-8 -*-

from odoo import models, fields, api

class HRShift(models.Model):
    _name = 'hr.shift'
    _description = 'Work Shift'

    name = fields.Char(string="Shift Name", required=True)
    start_time = fields.Float(string="Start Time", required=True)
    end_time = fields.Float(string="End Time", required=True)


class HRAttendance(models.Model):
    _inherit = 'hr.attendance'

    shift_type_id = fields.Many2one('hr.shift', string="Shift Type")