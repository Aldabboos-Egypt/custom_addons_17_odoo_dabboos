from odoo import fields, models

class AutoPurchaseWorkflow(models.Model):
    _name = 'sh.auto.purchase.workflow'

    name = fields.Char(string = "Name",required= True)
    validate_order = fields.Boolean(string = "Recipt Order")
    create_invoice = fields.Boolean(string = "Create Invoice")
    validate_invoice = fields.Boolean(string = "Validate Invoice")
    register_payment = fields.Boolean(string = "Register Payment")
    send_invoice_by_email = fields.Boolean(string = "Send Invoice By Email")
    purchase_journal = fields.Many2one('account.journal',string = "Purchase Journal",)
    payment_journal = fields.Many2one('account.journal',string = "Payment Journal",)
    payment_method = fields.Many2one('account.payment.method',string = "Payment Method")
    force_transfer = fields.Boolean(string = "Force Transfer")

