# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

from odoo import models, fields, _
from odoo.exceptions import UserError


class ShLawMatterMarkLostWizard(models.TransientModel):
    _name = "sh.law.matter.mark.lost.wizard"
    _description = "Mark Lost Reason Wizard"

    mark_lost = fields.Text("Reason", required=True)

    def reason_submit(self):
        context = self.env.context or {}
        if context and context.get("active_ids", False):
            active_ids = context.get("active_ids")
            law_request = self.env["sh.law.matter"].browse(active_ids)
            if law_request:
                law_request.write({
                    "mark_lost": self.mark_lost,
                    "state": "lost",
                })
        else:
            raise UserError(
                _("Programming error: wizard action executed without active_ids in context."))
