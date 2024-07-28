# -*- coding: utf-8 -*-
import base64
import time
from datetime import datetime

import requests
from odoo import models, fields, api, _
from celery import Celery

import threading
import time
import requests

app = Celery('tasks',
             broker='amqps://ixztbywk:R7EbdYRY25opibyrvT7ge2e_xeVRCNUd@fish.rmq.cloudamqp.com/ixztbywk')

image_typs = ['image/png', 'image/jpg', 'image/jpeg', 'image/gif', 'image/bmp', 'image/webp', ]


 

class WhatsAppMessage(models.Model):
    _name = 'whatsapp.campaign'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    _description = 'WhatsApp Message'

    name = fields.Char('Name', )
    account_id= fields.Many2one(
        comodel_name='whatsapp.account',
        string='Account ID',required=True
        )
    prefix = fields.Char(string='Prefix', required=True)

    template_id = fields.Many2one(
        comodel_name='whatsapp.campaign.template',
        string='Template',
        required=True)

    error_send_ids = fields.One2many(
        comodel_name='error.send',
        inverse_name='msgs_id',
        string='Error Send Msg',
        required=False)

    errors_count = fields.Integer(compute='_compute_data', string="Errors Count")
    contact_count = fields.Integer(compute='_compute_data', string="Contact Count")
    msg_timer = fields.Integer(string='Timer', default=2)
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        required=False)

    @api.depends("error_send_ids")
    def _compute_data(self):
        for rec in self:
            rec.errors_count = len(rec.error_send_ids)
            rec.contact_count = len(rec.partners)

    @api.onchange('template_id')
    def template_id_changed(self):
        if self.template_id:
            self.tags = self.template_id.tags.ids
            self.partners = self.template_id.partners.ids
            self.msg = self.template_id.msg
            self.attachment_ids = self.template_id.attachment_ids.ids
            self.prefix = self.template_id.prefix
            self.title = self.template_id.title
            self.company_id = self.template_id.company_id.id

    @api.model
    def create(self, vals):
        res = super(WhatsAppMessage, self).create(vals)
        if not res.name:
            today = datetime.now()
            month_year = today.strftime("%B_%Y")
            res.name = f"Msg{today.day}_{month_year}"
        return res

    tags = fields.Many2many('res.partner.category', string='Tags')
    title = fields.Many2one('res.partner.title')
    partners = fields.Many2many('res.partner', string='Partners', required=True,
                                domain="['&','&',('category_id', 'in', tags),('company_id', '=', company_id),('title', '=', title)]")
    msg = fields.Text(string='Message', required=True)

    attachment_ids = fields.Many2many('ir.attachment', string='Files  ')

    send_done = fields.Boolean(
        string='Sent Done', copy=False,
        required=False)

    def _get_attachment_type(self):

        images_attachment = self.attachment_ids.filtered(
            lambda x: x.mimetype in image_typs)
        file_attachments = self.attachment_ids.filtered(
            lambda x: x.mimetype not in image_typs)
        return file_attachments, images_attachment

    def action_view_error_details(self):
        return {
            'name': _('Error Details'),
            'view_mode': 'tree,form',
            'res_model': 'error.send',
            'views': [(False, 'tree'), (False, 'form')],
            'type': 'ir.actions.act_window',
            'domain': [('msgs_id', '=', self.id)],
        }

    def _check_send(self, number, response, partner):

        mobile_number = number.replace(" ", "")
        flag = False

        if mobile_number.startswith("+20"):
            if len(mobile_number) == 13:
                flag = True
        else:
            if len(mobile_number) == 11:
                flag = True

        if not flag:
            ids = self.error_send_ids.mapped('partner_id').ids

            if partner.id not in ids:
                self.env['error.send'].create({
                    'partner_id': partner.id,
                    'number': number,
                    'cause': "Mobile Number Format",
                    'msgs_id': self.id,

                })
                print("error", partner)

        for rec in self:
            if rec.errors_count == 0:
                rec.send_done = True
            else:
                rec.send_done = False

    # @app.task

    def send_whatsapp_message(self):
        self.error_send_ids = None

        def worker(partner, number, instance, token, full_msg, image_attachments, file_attachments):
            headers = {"content-type": "application/x-www-form-urlencoded"}
            chat_url = f"https://api.ultramsg.com/{instance}/messages/chat"
            doc_url = f"https://api.ultramsg.com/{instance}/messages/document"
            img_url = f"https://api.ultramsg.com/{instance}/messages/image"

            if image_attachments:
                if len(image_attachments) == 1:
                    data = {
                        "token": token,
                        "to": number,
                        "image": image_attachments[0].datas,
                        "caption": full_msg
                    }
                    response = requests.request("POST", img_url, data=data, headers=headers)
                    self._check_send(response=response, partner=partner, number=number)
                else:
                    for image in image_attachments:
                        data = {
                            "token": token,
                            "to": number,
                            "image": image.datas,
                        }
                        response = requests.request("POST", img_url, data=data, headers=headers)
                        self._check_send(response=response, partner=partner, number=number)

                    data = {
                        "token": token,
                        "to": number,
                        "body": full_msg
                    }
                    response = requests.request("POST", chat_url, data=data, headers=headers)
                    self._check_send(response=response, partner=partner, number=number)

            for file in file_attachments:
                data = {
                    "token": token,
                    "to": number,
                    "document": file.datas,
                    "filename": file.name
                }
                response = requests.request("POST", doc_url, data=data, headers=headers)
                self._check_send(response=response, partner=partner, number=number)

            if not image_attachments:
                data = {
                    "token": token,
                    "to": number,
                    "body": full_msg
                }
                response = requests.request("POST", chat_url, data=data, headers=headers)
                self._check_send(response=response, partner=partner, number=number)

            if self.msg_timer > 0:
                time.sleep(self.msg_timer)

        threads = []
        for partner in self.partners:
            number = partner.mobile
            instance = self.account_id.account_uid
            token = self.account_id.token

            if not number:
                ids = self.error_send_ids.mapped('partner_id').ids

                if partner.id not in ids:
                    self.env['error.send'].create({
                        'partner_id': partner.id,
                        'cause': "Mobile Number Not Found",
                        'msgs_id': self.id,
                    })
                continue

            full_msg = self.prefix + " " + self.msg
            file_attachments = self._get_attachment_type()[0]
            image_attachments = self._get_attachment_type()[1]

            if '+' not in number:
                number = str(partner.country_id.phone_code) + partner.mobile

            thread = threading.Thread(target=worker, args=(
            partner, number, instance, token, full_msg, image_attachments, file_attachments))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # All threads have completed here
        print("All messages sent successfully.")


class ErrorSend(models.Model):
    _name = 'error.send'
    _rec_name = 'partner_id'
    partner_id = fields.Many2one(comodel_name='res.partner', string='Partner', )
    cause = fields.Char(string='Cause', readonly=True)
    number = fields.Char(string='Number', readonly=True)

    msgs_id = fields.Many2one(
        comodel_name='whatsapp.campaign',
        string='Message',
    )


class WhatsTemplate(models.Model):
    _name = 'whatsapp.campaign.template'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Name', required=True)
    prefix = fields.Char(string='Prefix')
    title = fields.Many2one('res.partner.title')
    tags = fields.Many2many('res.partner.category', string='Tags')
    partners = fields.Many2many('res.partner', string='Partners', required=True,
                                domain="['&','&',('category_id', 'in', tags),('company_id', '=', company_id),('title', '=', title)]")
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        required=False)

    msg = fields.Text(string='Message', required=True)
    attachment_ids = fields.Many2many('ir.attachment', string='Attachments')


# class AccountPayment(models.Model):
#     _inherit = 'account.payment'
# 
#     attachment_ids = fields.Many2many(
#         'ir.attachment')
# 
#     def get_attachments(self):
#         #
#         # template = self.env.ref('account.email_template_edi_invoice')
#         # report = template.report_template_ids[0] if template.report_template_ids.ids else ''
#         report = self.env.ref('account.action_report_payment_receipt')
#         # report = self.env.ref('account.action_report_payment_receipt')
# 
#         Attachment = self.env['ir.attachment']
# 
#         report_xml_id = report.get_external_id()[report.id]
#         res, format = self.env['ir.actions.report'].with_context(
#             force_report_rendering=True)._render_qweb_pdf(report_xml_id, res_ids=[self.id])
#         res = base64.b64encode(res)
# 
#         attachments = []
# 
#         attachments.append((self.name, res))
#         attachment_ids = []
#         for attachment in attachments:
#             attachment_data = {
#                 'name': attachment[0],
#                 'datas': attachment[1],
#                 'type': 'binary',
#                 'res_model': 'account.payment',
#                 'res_id': self.id,
#             }
#             attachment_ids.append(Attachment.create(attachment_data).id)
#         if attachment_ids:
#             self.attachment_ids = [(6, 0, attachment_ids)]
# 
#         print(self.attachment_ids)
# 
#     def send_ws_msg(self):
# 
#         self.get_attachments()
#         number = self.partner_id.mobile
#         instance = self.env["ir.default"].sudo()._get('res.config.settings', 'instance')
#         print('instance', instance)
#         token = self.env["ir.default"].sudo()._get('res.config.settings', 'token')
#         print('token', token)
#         if number:
#             if '+' not in number:
#                 number = str(self.partner_id.country_id.phone_code) + self.partner_id.mobile
#         else:
#             raise models.ValidationError("Number Not found")
#         chat_url = f"https://api.ultramsg.com/{instance}/messages/chat"
#         doc_url = f"https://api.ultramsg.com/{instance}/messages/document"
#         msg = """
#             Hello  ,
#             I hope this message finds you well.
#             We would like to inform you that your invoice for service is now ready. Please find the attached payment invoice for your reference.
#             """
#         data = {
#             "token": token,
#             "body": msg,
#             "to": number,
#             "filename": 'payment.pdf',
#         }
#         headers = {"content-type": "application/x-www-form-urlencoded"}
#         chat_response = requests.request("POST", chat_url, data=data, headers=headers)
#         chat_res = chat_response.json()
#         print('chat_res', chat_res)
#         res_dict = {'chat_res': chat_res}
#         if self.attachment_ids.ids:
#             pdf_url = self.attachment_ids[0].datas
#             # pdf_url = report_url + '/report/pdf/' + 'roya_reports.sale_order_template_id/' + str(self.id)
#             data.update({"document": pdf_url, })
#             doc_response = requests.request("POST", doc_url, data=data, headers=headers)
#             doc_res = doc_response.json()
#             print('doc_res', doc_res)
#             res_dict.update({'doc_res': doc_res})
#         return self.attachment_ids
# 
#     def action_post(self):
#         res = super(AccountPayment, self).action_post()
#         self.send_ws_msg()
#         return res