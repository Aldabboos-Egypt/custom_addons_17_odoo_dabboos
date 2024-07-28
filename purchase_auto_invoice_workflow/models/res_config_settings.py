from odoo import fields, models,_,api


class ResCompany(models.Model):
    _inherit = 'res.company'

    group_auto_purchase_workflow = fields.Boolean("Enable Auto Workflow")
    purchase_workflow_id = fields.Many2one('sh.auto.purchase.workflow',string = "Default Workflow")

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    group_auto_purchase_workflow = fields.Boolean("Enable Auto Workflow",related = "company_id.group_auto_purchase_workflow",readonly = False,implied_group='purchase_auto_invoice_workflow.group_auto_purchase_workflow')
    purchase_workflow_id = fields.Many2one('sh.auto.purchase.workflow',string = "Default Workflow",related = "company_id.purchase_workflow_id",readonly = False)





