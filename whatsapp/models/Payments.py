import base64

from odoo import models, api
import requests

class AccountPayment(models.Model):
    _inherit = 'account.payment'

    # def action_post(self):
    #     super(AccountPayment, self).action_post()
    #     context = {
    #         'active_model': 'account.payment',
    #         'active_id': self.id,
    #         'default_payment_id': self.id,
    #         'phone': self.partner_id.phone,
    #     }
    #     return {
    #         'type': 'ir.actions.act_window',
    #         'name': 'Send WhatsApp Message',
    #         'res_model': 'whatsapp.composer',
    #         'view_mode': 'form',
    #         'views': [(False, 'form')],
    #         'target': 'new',
    #         'context': context,
    #     }

    def action_post(self):
        for payment in self:
            super(AccountPayment, payment).action_post()
            context = {
                'active_model': 'account.payment',
                'active_id': payment.id,
                'default_payment_id': payment.id,
            }
            whatsapp_composer = self.env['whatsapp.composer'].with_context(context).create({})

            if whatsapp_composer.wa_template_id.start_automatic_send:
                whatsapp_composer.action_send_whatsapp_template()

            if whatsapp_composer.wa_template_id.report_automatic_send:
                payment.ensure_one()  # Ensure we are working with a single payment record
                ir_actions_report_sudo = self.env['ir.actions.report'].sudo()
                report_sudo = self.env.ref('account.action_report_payment_receipt')
                pdf_content, _ = ir_actions_report_sudo._render_qweb_pdf(report_sudo, res_ids=payment.ids)
                b64_pdf = base64.b64encode(pdf_content)
                pdf_url = b64_pdf
                instance = whatsapp_composer.wa_account_id.account_uid
                token = whatsapp_composer.wa_account_id.token
                doc_url = f"https://api.ultramsg.com/{instance}/messages/document"
                headers = {"content-type": "application/x-www-form-urlencoded"}
                header_data = {
                    "token": token,
                    "document": pdf_url,
                    "filename": "payment.pdf",
                    "to": whatsapp_composer.phone,
                }
                requests.request("POST", doc_url, data=header_data, headers=headers)

        return True
