# -*- coding: utf-8 -*-

from odoo import fields, models


class ShLawErpCourts(models.Model):
    _name = "sh.law.erp.courts"
    _description = "Law Erp Courts"
    _order = "id desc"

    name = fields.Char(string="Court Name", required=True)
