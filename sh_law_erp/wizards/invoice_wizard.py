# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class ShLawMatterMarkLostWizard(models.TransientModel):
    _name = "sh.law.matter.invoice.wizard"
    _description = "Matter Invoice Wizard"

    def _get_default_currency_id(self):
        return self.env.company.currency_id.id

    client_id = fields.Many2one(
        "res.partner", string="Customer", required=True)
    matter_id = fields.Many2one(
        "sh.law.matter", string="Matter", readonly=True)
    lawyer_id = fields.Many2one("hr.employee", string="Lawyer", readonly=True)
    invoice_date = fields.Datetime("Invoice Date", default=fields.Datetime.now)
    payment_term_id = fields.Many2one(
        "account.payment.term", string="Payment Term")
    payment_by = fields.Selection(
        selection=[
            ("trial", "Per Trial"),
            ("case", "Per Case"),
            ("hour", "Per Hour"),
        ], string="Payment By", required=True
    )
    trials_ids = fields.Many2many("sh.law.erp.trial", string="Trials")
    hours = fields.Float("Hours", default=1.0, required=True)
    invoice_amt = fields.Monetary(string="Amount Per Case/Hour/Trial")
    total_invoice_amount = fields.Monetary(string="Total Invoice Amount")
    currency_id = fields.Many2one(
        "res.currency",
        default=_get_default_currency_id, required=True)

    @api.model
    def default_get(self, fields):
        res = super(ShLawMatterMarkLostWizard, self).default_get(fields)
        active_ids = self.env.context.get("active_ids")
        matter = self.env["sh.law.matter"].browse(active_ids)

        if matter:
            values = {
                "matter_id": matter.id,
                "client_id": matter.client_id.id if matter.client_id else False,
                "lawyer_id": matter.lawyer.id if matter.lawyer else False,
                "payment_by": matter.payment_by,

            }
            if matter.lawyer:
                amount = 0
                if matter.payment_by == "trial":
                    amount = matter.lawyer.wage_per_trial

                elif matter.payment_by == "case":
                    amount = matter.lawyer.wage_per_case

                elif matter.payment_by == "hour":
                    amount = matter.lawyer.wage_per_hour

                values.update({
                    "invoice_amt": amount
                })
            res.update(values)
        return res

    def create_invoice(self):
        if self:
            if not self.client_id or not self.matter_id or not self.lawyer_id or not self.payment_by:
                raise UserError(
                    _("Please Select Customer and Payment By first"))

        action = {
            "name": "Invoices",
            "type": "ir.actions.act_window",
            "res_model": "account.move",
            "view_mode": "form",
            "domain": [],
            "context": {
                "default_move_type": "out_invoice",
                "default_partner_id": self.client_id.id,
                "default_lawyer": self.lawyer_id.id,
                "default_payment_by": self.payment_by,
                "default_matter_id": self.matter_id.id,
                "default_trial_ids": [(6, 0, self.trials_ids.ids or [])],
                "default_hours": self.hours,
                "default_to_price_unit": self.invoice_amt,
                "default_invoice_payment_term_id": self.payment_term_id.id,
                },
            "target": "current",
        }
        return action

    @api.onchange("payment_by", "hours", "trials_ids",)
    def compute_per_amount_case_hour_trials(self):
        if self:
            amount = 0
            if self.lawyer_id:
                amount = 0
                if self.payment_by == "trial":
                    amount = self.lawyer_id.wage_per_trial

                elif self.payment_by == "case":
                    amount = self.lawyer_id.wage_per_case

                elif self.payment_by == "hour":
                    amount = self.lawyer_id.wage_per_hour

            self.invoice_amt = amount

    @api.onchange("invoice_amt", "payment_by", "hours", "trials_ids")
    def compute_total_invoice_amount(self):
        if self:
            amount = 0
            if self.payment_by == "trial":
                amount = self.invoice_amt
                amount = amount * len(self.trials_ids.ids)

            elif self.payment_by == "case":
                amount = self.invoice_amt

            elif self.payment_by == "hour":
                amount = self.invoice_amt
                amount = amount * self.hours

            self.total_invoice_amount = amount

    @api.constrains("hours")
    def check_value(self):
        for rec in self:
            if rec.hours < 0:
                raise ValidationError(_("Hours cannot be negative"))
            else:
                return rec.hours
