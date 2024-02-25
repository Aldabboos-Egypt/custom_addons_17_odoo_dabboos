# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

from odoo import models, fields, _

from odoo.exceptions import UserError


class ShLawClientRequestRejectWizard(models.TransientModel):
    _name = "sh.law.client.request.reject.wizard"
    _description = "Reject Reason Wizard"

    reject_reason = fields.Text("Reject Reason", required=True)

    def submit(self):
        context = self.env.context or {}
        if context and context.get("active_ids", False):
            active_ids = context.get("active_ids")
            law_request = self.env["sh.law.client.request"].browse(active_ids)
            if law_request:
                law_request.write({
                    "reject_reason": self.reject_reason,
                    "state": "reject",
                })
        else:
            raise UserError(
                _("Programming error: wizard action executed without active_ids in context."))
