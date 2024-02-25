# -*- coding: utf-8 -*-

from odoo import fields, models


class ShLawMetterType(models.Model):
    _name = "sh.law.matter.category"
    _description = "Law Matter Category"
    _order = "id desc"

    name = fields.Char(string="Matter Category", required=True)
