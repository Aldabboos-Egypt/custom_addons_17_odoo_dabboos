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

    def validate_contact(self, number, instance, token):

        headers = {"content-type": "application/x-www-form-urlencoded"}
        check_url = f"https://api.ultramsg.com/{instance}/contacts/check"

        # Format the number for the chatId (e.g., "1234567890@c.us")
        check_params = {
            "token": token,
            "chatId": number.replace("+", "") + "@c.us",  # Ensure proper chat ID format
            "nocache": "true"
        }

        try:
            response = requests.request("GET", check_url, headers=headers, params=check_params)
            if response.status_code == 200 and response.json().get('status') == "valid":
                return True
            return False
        except Exception as e:
            print(f"Error validating contact {number}: {e}")
            return False

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
            check_url = f"https://api.ultramsg.com/{instance}/contacts/check"

            # Validate contact number using the check endpoint
            check_params = {
                "token": token,
                "chatId": number.replace("+", "") + "@c.us",  # Ensure proper chat ID format
                "nocache": "true"
            }
            response = requests.request("GET", check_url, headers=headers, params=check_params)

            # Parse response from the check endpoint
            if response.status_code != 200 or response.json().get('status') != "valid":
                # Log invalid or unregistered numbers
                ids = self.error_send_ids.mapped('partner_id').ids
                if partner.id not in ids:
                    self.env['error.send'].create({
                        'partner_id': partner.id,
                        'number': number,
                        'cause': "Invalid or Unregistered Number",
                        'msgs_id': self.id,
                    })
                print(f"Error: {partner.name} has an invalid number: {number}")
                return

            # Send images if provided
            if image_attachments:
                if len(image_attachments) == 1:
                    data = {
                        "token": token,
                        "to": number,
                        "image": image_attachments[0].datas,
                        "caption": full_msg
                    }
                    response = requests.request("POST", img_url, data=data, headers=headers)
                else:
                    for image in image_attachments:
                        data = {
                            "token": token,
                            "to": number,
                            "image": image.datas,
                        }
                        response = requests.request("POST", img_url, data=data, headers=headers)

                    data = {
                        "token": token,
                        "to": number,
                        "body": full_msg
                    }
                    response = requests.request("POST", chat_url, data=data, headers=headers)

            # Send files if provided
            for file in file_attachments:
                data = {
                    "token": token,
                    "to": number,
                    "document": file.datas,
                    "filename": file.name
                }
                response = requests.request("POST", doc_url, data=data, headers=headers)

            # Send the main message if no images
            if not image_attachments:
                data = {
                    "token": token,
                    "to": number,
                    "body": full_msg
                }
                response = requests.request("POST", chat_url, data=data, headers=headers)

            # Delay between messages if configured
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
