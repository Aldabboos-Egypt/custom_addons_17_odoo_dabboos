# Part of Odoo. See LICENSE file for full copyright and licensing details.

import re
import logging

from ast import literal_eval

import requests
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, RedirectWarning, UserError
from odoo.addons.whatsapp.tools import phone_validation as wa_phone_validation
import re
import logging

from ast import literal_eval

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, RedirectWarning
from odoo.addons.phone_validation.tools import phone_validation


_logger = logging.getLogger(__name__)


class WhatsAppComposer(models.TransientModel):
    _name = 'whatsapp.composer'
    _description = 'Send WhatsApp Wizard'


    @api.model
    def _get_default_wa_account_id(self):
        first_account = self.env['whatsapp.account'].search([
            ('allowed_company_ids', 'in', self.env.companies.ids)], limit=1)
        return first_account.id if first_account else False


    wa_account_id = fields.Many2one(comodel_name='whatsapp.account', string="Account", default=_get_default_wa_account_id,required=True)


    @api.model
    def default_get(self, fields):
        result = super().default_get(fields)
        context = self.env.context
        if context.get('active_model'):
            result['res_model'] = context['active_model']
            wa_template_id = self.env['whatsapp.template']._find_default_for_model(result['res_model'])
            if wa_template_id and not result.get('wa_template_id'):
                result['wa_template_id'] = wa_template_id.id
            elif not wa_template_id and not result.get('wa_template_id'):
                if self.env.user.has_group('whatsapp.group_whatsapp_admin'):
                    raise RedirectWarning(
                        _("No approved WhatsApp Templates are available for this model."),
                        self.env.ref('whatsapp.whatsapp_template_action').id,
                        _("Configure Templates"),
                        {'search_default_model': result['res_model']}
                    )
                else:
                    raise ValidationError(_("No approved WhatsApp Templates are available for this model."))
        if context.get('active_ids') or context.get('active_id'):
            result['res_ids'] = context.get('active_ids') or [context.get('active_id')]
        if context.get('active_ids') and len(context['active_ids']) > 1:
            result['batch_mode'] = True
        return result

    # documents
    attachment_id = fields.Many2one('ir.attachment', index=True)
    res_ids = fields.Char('Document IDs', required=True)
    res_model = fields.Char('Document Model Name', required=True)
    batch_mode = fields.Boolean("Is Multiple Records")

    # content
    phone = fields.Char(string="Phone", compute="_compute_number", readonly=False, store=True)
    invalid_phone_number_count = fields.Integer(compute="_compute_invalid_phone_number_count")
    wa_template_id = fields.Many2one(comodel_name="whatsapp.template", string="Template",required=True)
    preview_whatsapp = fields.Html(compute="_compute_preview_whatsapp", string="Message Preview")

    #free texts
    number_of_free_text = fields.Integer(string="Number of free text", compute='_compute_number_of_free_text')
    number_of_free_text_button = fields.Integer(string="Number of free text Buttons", compute='_compute_number_of_free_text_button')
    is_header_free_text = fields.Boolean(compute='_compute_is_header_free_text')
    is_button_dynamic = fields.Boolean(compute='_compute_is_button_dynamic')
    header_text_1 = fields.Char(string="Header Free Text", compute='_compute_free_text', store=True)
    free_text_1 = fields.Char(string="Free Text 1", compute='_compute_free_text', store=True)
    free_text_2 = fields.Char(string="Free Text 2", compute='_compute_free_text', store=True)
    free_text_3 = fields.Char(string="Free Text 3", compute='_compute_free_text', store=True)
    free_text_4 = fields.Char(string="Free Text 4", compute='_compute_free_text', store=True)
    free_text_5 = fields.Char(string="Free Text 5", compute='_compute_free_text', store=True)
    free_text_6 = fields.Char(string="Free Text 6", compute='_compute_free_text', store=True)
    free_text_7 = fields.Char(string="Free Text 7", compute='_compute_free_text', store=True)
    free_text_8 = fields.Char(string="Free Text 8", compute='_compute_free_text', store=True)
    free_text_9 = fields.Char(string="Free Text 9", compute='_compute_free_text', store=True)
    free_text_10 = fields.Char(string="Free Text 10", compute='_compute_free_text', store=True)
    button_dynamic_url_1 = fields.Char(string="Button Url 1", compute='_compute_button_dynamic_url', store=True)
    button_dynamic_url_2 = fields.Char(string="Button Url 2", compute='_compute_button_dynamic_url', store=True)

    # ------------------------------------------------------------
    # COMPUTES
    # ------------------------------------------------------------

    @api.depends('wa_template_id')
    @api.depends_context('default_phone')
    def _compute_number(self):
        """ In single mode, 'phone' is the number to contact (can be set through
        context, for example when forced through UI). In multi mode it is more
        an informational field, holding the first record found numbers. """
        for composer in self:
            records = self.env[composer.res_model].browse(literal_eval(composer.res_ids))
            numbers = []
            for record in records[:12]:
                if composer.wa_template_id.phone_field:
                    try:
                        numbers.append(record._find_value_from_field_path(composer.wa_template_id.phone_field))
                    except UserError as err:
                        error_msg = _("Template %(template_name)s holds a wrong configuration for 'phone field'\n%(error_msg)s",
                                      template_name=composer.wa_template_id.name,
                                      error_msg=err.args[0]
                                     )
                        raise ValidationError(error_msg) from err
            if not composer.batch_mode:
                phone = self.env.context.get('default_phone')
                if not phone:
                    phone = numbers[0] if numbers and numbers[0] else composer.phone
            elif not numbers:
                phone = False
            else:
                other_count = len(records) - len(numbers)
                phone = ', '.join(self._extract_digits(num) for num in numbers if num)
                if other_count:
                    phone += _(", ... (%s Others)", other_count)
            composer.phone = phone

    @api.depends('phone', 'batch_mode')
    def _compute_invalid_phone_number_count(self):
        for composer in self:
            records = self._get_active_records()
            if composer.batch_mode:
                invalid_phone_number_count = 0
                for rec in records:
                    mobile_number = rec._find_value_from_field_path(composer.wa_template_id.phone_field)
                    mobile_number = wa_phone_validation.wa_phone_format(
                        rec, number=mobile_number or '',
                        raise_exception=False,
                    ) if mobile_number else False
                    if not mobile_number:
                        invalid_phone_number_count += 1
            elif composer.phone:
                sanitize_number = wa_phone_validation.wa_phone_format(
                    records, number=composer.phone,
                    raise_exception=False,
                )
                invalid_phone_number_count = 1 if not sanitize_number else 0
            else:
                invalid_phone_number_count = 1
            composer.invalid_phone_number_count = invalid_phone_number_count

    @api.depends(lambda self: self._get_free_text_fields())
    def _compute_preview_whatsapp(self):
        """This method is used to compute the preview of the whatsapp message."""
        for record in self:
            rec = record._get_active_records()
            if record.wa_template_id and rec:
                record.preview_whatsapp = self.env['ir.qweb']._render('whatsapp.template_message_preview', {
                    'body': record._get_html_preview_whatsapp(rec=rec[0]),
                    'buttons': record.wa_template_id.button_ids,
                    'header_type': record.wa_template_id.header_type,
                    'footer_text': record.wa_template_id.footer_text,
                    'language_direction': 'rtl' if record.wa_template_id.lang_code in ('ar', 'he', 'fa', 'ur') else 'ltr',
                })
            else:
                record.preview_whatsapp = None

    @api.depends('wa_template_id')
    def _compute_number_of_free_text_button(self):
        for rec in self:
            tmpl_vars = rec.wa_template_id.variable_ids
            rec.number_of_free_text_button = len(tmpl_vars.filtered(lambda var: var.field_type == 'free_text' and var.line_type == 'button'))

    @api.depends('wa_template_id')
    def _compute_number_of_free_text(self):
        for rec in self:
            if rec.wa_template_id:
                rec.number_of_free_text = len(rec.wa_template_id.variable_ids.filtered(lambda line: line.field_type == 'free_text' and line.line_type == 'body'))
            else:
                rec.number_of_free_text = 0

    @api.depends('wa_template_id')
    def _compute_is_header_free_text(self):
        for rec in self:
            if rec.wa_template_id and rec.wa_template_id.variable_ids and rec.wa_template_id.variable_ids.filtered(lambda line: line.field_type == 'free_text' and line.line_type == 'header'):
                rec.is_header_free_text = True
            else:
                rec.is_header_free_text = False

    @api.depends('wa_template_id')
    def _compute_is_button_dynamic(self):
        for rec in self:
            if rec.wa_template_id and rec.wa_template_id.variable_ids and rec.wa_template_id.variable_ids.filtered(lambda line: line.field_type == 'free_text' and line.line_type == 'button'):
                rec.is_button_dynamic = True
            else:
                rec.is_button_dynamic = False

    @api.depends('wa_template_id')
    def _compute_button_dynamic_url(self):
        for rec in self:
            freetext_btn_vars = rec.wa_template_id.variable_ids.filtered(lambda line: line.line_type == 'button' and line.field_type == 'free_text')
            if not rec.button_dynamic_url_1:
                rec.button_dynamic_url_1 = freetext_btn_vars[0].demo_value if len(freetext_btn_vars) > 0 else ''
            if not rec.button_dynamic_url_2:
                rec.button_dynamic_url_2 = freetext_btn_vars[1].demo_value if len(freetext_btn_vars) > 1 else ''

    @api.depends('wa_template_id')
    def _compute_free_text(self):
        for rec in self:
            if rec.wa_template_id.header_type == 'text':
                header_params = rec.wa_template_id.variable_ids.filtered(lambda line: line.line_type == 'header')
                if rec.wa_template_id.variable_ids and header_params:
                    header_param = header_params[0]
                    if header_param.field_type == 'free_text' and not rec.header_text_1:
                        rec.header_text_1 = header_param.demo_value
            if rec.wa_template_id.variable_ids:
                free_text_count = 1
                for param in rec.wa_template_id.variable_ids.filtered(lambda line: line.line_type == 'body' and line.field_type == 'free_text'):
                    if not rec[f"free_text_{free_text_count}"]:
                        rec[f"free_text_{free_text_count}"] = param.demo_value
                    free_text_count += 1

    def _extract_digits(self, string):
        if not string:
            return string
        matches = re.findall(r"\d+", string)
        result = "".join(matches)
        return result

    def _get_free_text_fields(self):
        return ["wa_template_id", "header_text_1", "button_dynamic_url_1", "button_dynamic_url_2"] + [f"free_text_{i}" for i in range(1, 11)]

    # ------------------------------------------------------------
    # SEND MESSAGES
    # ------------------------------------------------------------

    def action_send_whatsapp_template(self):
        self.ensure_one()
        return self._send_whatsapp_template()


    def _send_whatsapp_template(self, force_send_by_cron=False):
        records = self._get_active_records()

        if self.wa_template_id and self.wa_template_id.variable_ids:
            field_types = self.wa_template_id.variable_ids.mapped('field_type')
            if 'user_mobile' in field_types and not self.env.user.mobile:
                raise ValidationError(
                    _("User mobile number required in template but no value set on user profile.")
                )
        free_text_json = self._get_text_free_json()
        message_vals = []
        company_country_id = self.env.company.country_id
        for rec in records:
            mobile_number = rec.mapped(self.wa_template_id.phone_field)[0] if self.batch_mode else self.phone
            formatted_number = phone_validation.phone_format(mobile_number, company_country_id.code, company_country_id.phone_code) if mobile_number else False
            if not formatted_number:
                continue
            body = self._get_html_preview_whatsapp(rec=rec)
            post_values = {
                'attachment_ids': [self.attachment_id.id] if self.attachment_id else [],
                'body': body,
                'message_type': 'whatsapp_message',
                'partner_ids': hasattr(rec, '_mail_get_partners') and rec._mail_get_partners()[rec.id].ids or rec._whatsapp_get_responsible().partner_id.ids,
            }
            if hasattr(records, '_message_log'):
                message = rec._message_log(**post_values)
            else:
                message = self.env['mail.message'].create(
                    dict(post_values, res_id=rec.id, model=self.res_model,
                         subtype_id=self.env['ir.model.data']._xmlid_to_res_id("mail.mt_note"))
                )
            message_vals.append({
                'mail_message_id': message.id,
                'mobile_number': mobile_number,
                'free_text_json': free_text_json,
                'wa_template_id': self.wa_template_id.id,
                'state': 'sent',
                'wa_account_id': self.wa_template_id.wa_account_id.id,
            })
        if message_vals:
            def extract_text_from_html(html):
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(html, 'html.parser')
                text = soup.get_text(separator="\n").strip()
                return text
                # Extract text from HTML snippet
            formatted_text = extract_text_from_html(body)
            final_message = f"{formatted_text}\n\n{self.wa_template_id.footer_text}"

            header_chat_data=''
            if self.wa_template_id.header_type  in ('document' ,'image' , 'video'):
                header_chat_data =self.wa_template_id.header_attachment_ids

                print(self.wa_template_id.header_attachment_ids.datas)

            if self.wa_template_id.header_type =='text':
                header_chat_data = f"{formatted_text}\n\n{self.wa_template_id.header_text}"



            self.send_ws_msg(message=final_message,header_chat=header_chat_data, number=mobile_number)
            message = self.env['whatsapp.message'].create(message_vals)


            # message._send(force_send_by_cron=force_send_by_cron)


    def send_ws_msg(self,message,header_chat,number  ):
        #
        # instance = "instance71676"
        # token = "grlv10mh1tc04319"
        instance = self.wa_account_id.account_uid
        token = self.wa_account_id.token


        chat_url = f"https://api.ultramsg.com/{instance}/messages/chat"
        header_chat_url=None
        data = {
            "token": token,
            "body": message,
            "to": number,

        }

        header_data = {
            "token": token,
            "body": message,
            "to": number,

        }



        headers = {"content-type": "application/x-www-form-urlencoded"}

        if self.wa_template_id.header_type =='text':
            header_chat_url = f"https://api.ultramsg.com/{instance}/messages/chat"


        if self.wa_template_id.header_type =='image':

            header_data = {
                "token": token,
                "image": header_chat.datas,
                "to": number,
            }
            header_chat_url = f"https://api.ultramsg.com/{instance}/messages/image"

            requests.request("POST", header_chat_url, data=header_data, headers=headers)

        elif self.wa_template_id.header_type in ('document' , 'video'):
            header_chat_url = f"https://api.ultramsg.com/{instance}/messages/document"
            header_data = {
                "token": token,
                "document": header_chat.datas,
                "filename": header_chat.name,
                "to": number,
            }
            requests.request("POST", header_chat_url, data=header_data, headers=headers)
        elif self.wa_template_id.header_type =='text':
            header_chat_url = f"https://api.ultramsg.com/{instance}/messages/chat"

            header_data = {
                "token": token,
                "document": header_chat,
                 "to": number,
            }
            requests.request("POST", header_chat_url, data=header_data, headers=headers)
        else:
            pass

        chat_response = requests.request("POST", chat_url, data=data, headers=headers)
        chat_res = chat_response.json()
        print('chat_res', chat_res)
        if "error" in chat_res:
            raise UserError(str(chat_res["error"]))

        # if self.attachment_ids.ids:
        #     pdf_url = self.attachment_ids[0].datas
        #     # pdf_url = report_url + '/report/pdf/' + 'roya_reports.sale_order_template_id/' + str(self.id)
        #     data.update({"document": pdf_url, })
        #     doc_response = requests.request("POST", doc_url, data=data, headers=headers)
        #     doc_res = doc_response.json()
        #     print('doc_res', doc_res)
        #     res_dict.update({'doc_res': doc_res})
        # return self.attachment_ids

    def _get_text_free_json(self):
        """This method is used to prepare free text json using values set in free text field of composer."""
        self.ensure_one()
        json_vals = {}
        if self.header_text_1:
            json_vals['header_text'] = self.header_text_1
        if self.number_of_free_text:
            free_text_field = [f"free_text_{i + 1}" for i in range(self.number_of_free_text)]
            for value in free_text_field:
                if self[value]:
                    json_vals[value] = self[value]
        if self.button_dynamic_url_1:
            json_vals['button_dynamic_url_1'] = self.button_dynamic_url_1
        if self.button_dynamic_url_2:
            json_vals['button_dynamic_url_2'] = self.button_dynamic_url_2
        return json_vals

    def _get_html_preview_whatsapp(self, rec):
        """This method is used to get the html preview of the whatsapp message."""
        self.ensure_one()
        template_variables_value = self.wa_template_id.variable_ids._get_variables_value(rec)
        text_vars = self.wa_template_id.variable_ids.filtered(lambda var: var.field_type == 'free_text')
        for var_index, body_text_var in zip(range(1, self.number_of_free_text + 1), text_vars.filtered(lambda var: var.line_type == 'body')):
            free_text_x = self[f'free_text_{var_index}']
            if free_text_x:
                template_variables_value[f'body-{body_text_var.name}'] = free_text_x
        if self.header_text_1 and text_vars.filtered(lambda var: var.line_type == 'header'):
            template_variables_value['header-{{1}}'] = self.header_text_1
        return self.wa_template_id._get_formatted_body(variable_values=template_variables_value)

    # ------------------------------------------------------------
    # TOOLS
    # ------------------------------------------------------------

    def _get_active_records(self):
        self.ensure_one()
        return self.env[self.res_model].browse(literal_eval(self.res_ids))

