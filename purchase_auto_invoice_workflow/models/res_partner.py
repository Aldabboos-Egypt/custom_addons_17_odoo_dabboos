from odoo import fields, models,_

class ResPartner(models.Model):
    _inherit = 'res.partner'

    purchase_workflow_id = fields.Many2one('sh.auto.purchase.workflow',string = "Purchase Workflow")
    
