from datetime import datetime

from odoo import fields, models,_,api
from odoo.exceptions import UserError, ValidationError


MAP_INVOICE_TYPE_PARTNER_TYPE = {
    'out_invoice': 'customer',
    'out_refund': 'customer',
    'out_receipt': 'customer',
    'in_invoice': 'supplier',
    'in_refund': 'supplier',
    'in_receipt': 'supplier',
}

class Purchaseorder(models.Model):
    _inherit = 'purchase.order'

    purchase_workflow_id = fields.Many2one('sh.auto.purchase.workflow',string = "purchase Workflow")
    is_boolean = fields.Boolean(related = "company_id.group_auto_purchase_workflow")

    @api.onchange('partner_id')
    def get_workflow(self):
        if self.partner_id.purchase_workflow_id:
            if self.company_id.group_auto_purchase_workflow:
                self.purchase_workflow_id = self.partner_id.purchase_workflow_id
        else:
            if self.company_id.group_auto_purchase_workflow and self.company_id.purchase_workflow_id:
                self.purchase_workflow_id = self.company_id.purchase_workflow_id

    def button_confirm(self):
        res = super(Purchaseorder,self).button_confirm()
        if self.purchase_workflow_id:
            if self.purchase_workflow_id.validate_order and self.picking_ids:
                if self.purchase_workflow_id.force_transfer:
                    for picking in self.picking_ids:
                        for stock_move in picking.move_ids_without_package:
                            if stock_move.move_line_ids:
                                stock_move.move_line_ids.update({
                                    'qty_done':stock_move.product_uom_qty,
                                })
                            else:
                                self.env['stock.move.line'].create({
                                    'picking_id':picking.id,
                                    'move_id':stock_move.id,
                                    'date':stock_move.date,
                                    'reference':stock_move.reference,
                                    'origin':stock_move.origin,
                                    'qty_done':stock_move.product_uom_qty,
                                    'product_id':stock_move.product_id.id,
                                    'product_uom_id':stock_move.product_uom.id,
                                    'location_id':stock_move.location_id.id,
                                    'location_dest_id':stock_move.location_dest_id.id
                                })
                        picking.button_validate()
                        if picking.state != 'done':
                            sms = self.env['confirm.stock.sms'].create({
                                'pick_ids': [(4, picking.id)],
                            })
                            sms.send_sms()
                            picking.button_validate()

                else:
                    for picking in self.picking_ids:
                        picking.button_validate()
                        wiz = self.env['stock.immediate.transfer'].create({
                            'pick_ids': [(4, picking.id)],
                            'immediate_transfer_line_ids':[(0,0,{
                                'picking_id':picking.id,
                                'to_immediate':True,
                                })]
                            })
                        wiz.with_context(button_validate_picking_ids=picking.ids).process()

                        if picking.state != 'done':
                            sms = self.env['confirm.stock.sms'].create({
                                'pick_ids': [(4, picking.id)],
                            })
                            sms.send_sms()
                            ret = picking.button_validate()
                            if 'res_model' in ret and ret['res_model'] == 'stock.backorder.confirmation':
                                backorder_wizard = self.env['stock.backorder.confirmation'].create({
                                    'pick_ids':[(4,picking.id)],
                                    'backorder_confirmation_line_ids':[(0,0,{
                                        'picking_id':picking.id,
                                        'to_backorder':True,

                                    })]
                                })
                                backorder_wizard.with_context(button_validate_picking_ids=picking.ids).process()


            if self.purchase_workflow_id.create_invoice:
                self.action_create_invoice()
                invoice = self.invoice_ids[-1]
                invoice.invoice_date=datetime.now().date()

                if  self.purchase_workflow_id.purchase_journal:
                    invoice.write({
                        'journal_id' : self.purchase_workflow_id.purchase_journal.id
                    })

                if self.purchase_workflow_id.validate_invoice:
                    invoice.action_post()

                    if self.purchase_workflow_id.send_invoice_by_email:
                        template_id = self.env.ref('account.email_template_edi_invoice')
                        template_id.with_context(model_description='').sudo().send_mail(invoice.id, force_send=True,notif_layout="mail.mail_notification_paynow")

                    if self.purchase_workflow_id.register_payment:


                        # payment_methods = self.env['account.payment.method'].search([('payment_type','=','inbound')])
                        # journal = self.env['account.journal'].search([('type','in',('bank','cash'))])
                        payment = self.env['account.payment'].create({
                            'currency_id': invoice.currency_id.id,
                            'amount':invoice.amount_total,
                            'payment_type': 'outbound',
                            'partner_id': invoice.commercial_partner_id.id,
                            'partner_type': MAP_INVOICE_TYPE_PARTNER_TYPE[invoice.move_type],
                            'ref': invoice.payment_reference or invoice.name,
                            'payment_method_id':self.purchase_workflow_id.payment_method.id,
                            'journal_id':self.purchase_workflow_id.payment_journal.id
                        })

                        payment.action_post()
                        line_id = payment.line_ids.filtered(lambda l: l.debit)
                        invoice.js_assign_outstanding_line(line_id.id)
                        print(payment)

                        

