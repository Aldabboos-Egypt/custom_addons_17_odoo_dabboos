import ast
import base64
import functools
import json
import logging
import re
from datetime import datetime

import werkzeug
from odoo import http
from odoo.addons.dabbos_restapi.common import extract_arguments, invalid_response, valid_response
from odoo.exceptions import AccessError
from odoo.http import request
from werkzeug.utils import secure_filename
_logger = logging.getLogger(__name__)
from datetime import datetime, date  # Import date from datetime

def validate_token(func):
    @functools.wraps(func)
    def wrap(self, *args, **kwargs):
        access_token = kwargs.get("access_token")
        if not access_token:
            return invalid_response("access_token_not_found", "missing access token in request params", 401)
        access_token_data = request.env["api.access_token"].sudo().search([("token", "=", access_token)],
                                                                          order="id DESC", limit=1)
        if access_token_data.find_one_or_create_token(user_id=access_token_data.user_id.id) != access_token:
            return invalid_response("access_token", "token seems to have expired or invalid", 401)

        request.session.uid = access_token_data.user_id.id
        # request.uid = access_token_data.user_id.id
        request.update_env(user=access_token_data.user_id.id)
        return func(self, *args, **kwargs)

    return wrap

_routes = ["/<model>", "/<model>/<id>", "/<model>/<id>/<action>"]




class APIController(http.Controller):
    """."""
    def get_allowed_fields(self,fetch_id):

        return [rec.name for rec in fetch_id.field_ids]


    def __init__(self):
        self._model = "ir.model"



    @validate_token
    @http.route("/general", methods=["GET"], type="http", auth="none", csrf=False)
    def get(self,**kwargs):
        model = kwargs.get("model")
        domain_fields_dict = kwargs.get("domain")
        fetch_id = request.env['fetch.data'].sudo().search([("model_id.model", "=", model)], limit=1)

        if not fetch_id:
            return invalid_response(
                "invalid object model", "The model %s is not available in the registry." % model,
            )
        domain = []

        if domain_fields_dict:
            domain_fields_dict = ast.literal_eval(domain_fields_dict)
            domain_fields_keys = list(domain_fields_dict.keys())
            for rec in range(0, len(domain_fields_keys) - 1):
                domain += ['&']
            for key in domain_fields_keys:
                if type(domain_fields_dict.get(key)) is list:
                    domain += [(key, 'in', domain_fields_dict.get(key))]

                elif isinstance(domain_fields_dict.get(key), int):
                    domain += [(key, '=', domain_fields_dict.get(key))]

                else:
                    domain += [(key, 'ilike', domain_fields_dict.get(key))]

        try:
            ioc_name = model
            model = request.env[self._model].sudo().search([("model", "=", model)], limit=1, order='id desc')
            if model:
                print(domain)

                # domain, fields, offset, limit, order = extract_arguments(**payload)
                data = request.env[model.model].sudo().search_read(
                    domain=domain, fields=self.get_allowed_fields(fetch_id), order='id desc'
                )

                if data:
                    return valid_response(data)
                else:
                    return valid_response(data)
            return invalid_response(
                "invalid object model", "The model %s is not available in the registry." % ioc_name,
            )
        except AccessError as e:

            return invalid_response("Access error", "Error: %s" % e)

    @validate_token
    @http.route("/salesperson/get_products_categories", methods=["GET"], type="http", auth="none", csrf=False)
    def get_products_categories(self,**kwargs):
        category_id = int(kwargs.get("category_id"))
        pricelist_id = int(kwargs.get("pricelist_id"))
        user_id = int(kwargs.get("user_id"))

        print(category_id,pricelist_id,user_id)

        data_input = all([category_id, pricelist_id, user_id])
        if not data_input:
            # Empty 'db' or 'username' or 'password:
            return invalid_response(
                "missing error", "either of the following are missing [category_id, pricelist_id,user_id]", 403,
            )

        def get_all_child_ids(category):
            child_ids = category.ids
            for child_category in category.child_id:
                child_ids += get_all_child_ids(child_category)
            return child_ids

        category_id_object = request.env['product.category'].sudo().browse(int(category_id))

        if category_id_object.child_id:
            all_child_ids = get_all_child_ids(category_id_object)
            domain = ['|', ('categ_id', '=', int(category_id)), ('categ_id', 'in', all_child_ids)]
        else:
            domain = [('categ_id', '=', int(category_id))]

        pricelist = request.env['product.pricelist'].sudo().browse(pricelist_id)
        if not pricelist:
            return invalid_response(
                "Pricelist Not Found", 403,
            )
        product_ids = request.env['product.product'].sudo().search(domain)
        all_product_list = []
        for product in product_ids:
            line = pricelist.item_ids.filtered(lambda line: line.product_tmpl_id.product_variant_id.id == product.id)
            if line:
                all_product_list.append(
                    {
                        'ID_1': product.id,
                        'Name_1': product.name,
                        'Pricelist_Price': line.fixed_price,
                        'Pricelist': True,

                    }
                )
            else:
                all_product_list.append(
                    {
                        'ID_1': product.id,
                        'Name_1': product.name,
                        'Pricelist_Price': product.lst_price,
                        'Pricelist': False,

                    }
                )

        location_ids = request.env['res.users'].sudo().browse(user_id).allowed_locations

        quants = request.env['stock.quant'].sudo().search([
            ('location_id', 'in', location_ids.ids), ('product_id', '=', product_ids.ids)
        ])

        # Create a dictionary to store product quantities
        quantities = {}

        # Iterate through quants and update the quantities dictionary
        for quant in quants:
            if quant.product_id.id not in quantities:
                quantities[quant.product_id.id] = quant.available_quantity
            else:
                quantities[quant.product_id.id] += quant.available_quantity

        for item in all_product_list:
            item['QTY_1'] = quantities.get(item.get('ID_1'), 0)

        d2 = all_product_list

        model = 'product.product'
        fetch_id = request.env['fetch.data'].sudo().search([("model_id.model", "=", model)], limit=1)
        if not fetch_id:
            return invalid_response(
                "invalid object model", "The model %s is not available in the registry." % model,
            )
        field_names = [rec.name for rec in fetch_id.field_ids]
        d1 = request.env['product.product'].sudo().search_read(domain=[('id', 'in', product_ids.ids)], fields=field_names, )

        d1_dict = {item['id']: item for item in d1}

        # Merge d2 into d1 based on 'id'
        merged_data = []
        for item_d2 in d2:
            id_d2 = item_d2.get('ID_1')
            if id_d2 in d1_dict:
                item_d1 = d1_dict[id_d2]
                item_d1.update(item_d2)  # Merge the dictionaries
                merged_data.append(item_d1)


        return valid_response(data=merged_data)

    @validate_token
    @http.route("/salesperson/product_price", methods=["GET"], type="http", auth="none", csrf=False)
    def get_product_price(self,**kwargs):

        # image_url = "http://lenovo-legion:8017/web/image?model=product.product&id=2123&field=image_1920"
        #
        # return image_url


        pricelist_id = int(kwargs.get("pricelist_id"))
        user_id = int(kwargs.get("user_id"))

        data_input = all([pricelist_id, user_id])
        if not data_input:
            # Empty 'db' or 'username' or 'password:
            return invalid_response(
                "missing error", "either of the following are missing [category_id, pricelist_id,user_id]", 403,
            )

        pricelist = request.env['product.pricelist'].sudo().browse(pricelist_id)
        if not pricelist:
            return invalid_response(
                "Pricelist Not Found", 403,
            )
        product_ids = request.env['product.product'].sudo().search([])
        all_product_list = []
        for product in product_ids:
            line = pricelist.item_ids.filtered(lambda line: line.product_tmpl_id.product_variant_id.id == product.id)
            if line:
                all_product_list.append(
                    {
                        'ID_1': product.id,
                        'Name_1': product.name,
                        'Pricelist_Price': line.fixed_price,
                        'Pricelist': True,

                    }
                )
            else:
                all_product_list.append(
                    {
                        'ID_1': product.id,
                        'Name_1': product.name,
                        'Pricelist_Price': product.lst_price,
                        'Pricelist': False,

                    }
                )

        location_ids = request.env['res.users'].sudo().browse(user_id).allowed_locations


        quants = request.env['stock.quant'].sudo().search([
            ('location_id', 'in', location_ids.ids), ('product_id', '=', product_ids.ids)
        ])

        # Create a dictionary to store product quantities
        quantities = {}

        # Iterate through quants and update the quantities dictionary
        for quant in quants:
            if quant.product_id.id not in quantities:
                quantities[quant.product_id.id] = quant.available_quantity
            else:
                quantities[quant.product_id.id] += quant.available_quantity

        for item in all_product_list:
            item['QTY_1'] = quantities.get(item.get('ID_1'), 0)

        d2 = all_product_list

        model = 'product.product'
        fetch_id = request.env['fetch.data'].sudo().search([("model_id.model", "=", model)], limit=1)
        if not fetch_id:
            return invalid_response(
                "invalid object model", "The model %s is not available in the registry." % model,
            )
        field_names = [rec.name for rec in fetch_id.field_ids]
        d1 = request.env['product.product'].sudo().search_read(domain=[('id', 'in', product_ids.ids)], fields=field_names, )

        d1_dict = {item['id']: item for item in d1}

        # Merge d2 into d1 based on 'id'
        merged_data = []
        for item_d2 in d2:
            id_d2 = item_d2.get('ID_1')
            if id_d2 in d1_dict:
                item_d1 = d1_dict[id_d2]
                item_d1.update(item_d2)  # Merge the dictionaries
                merged_data.append(item_d1)


        return valid_response(data=merged_data)

    @validate_token
    @http.route("/salesperson/get_product_uoms", methods=["GET"], type="http", auth="none", csrf=False)
    def get_product_uoms(self,**kwargs  ):

        product_id = int(kwargs.get("product_id"))

        if not product_id:
            return invalid_response(
                "Missing Product Id.",
            )


        product_id=request.env['product.product'].sudo().browse(product_id)
        if not product_id:
            return invalid_response(
                "  Product Id Not Found.",
            )
        domain = [('category_id', '=', product_id.uom_id.category_id.id)]
        uom_ids=request.env['uom.uom'].sudo().search(domain)

        uom_data=[]
        for uom_id in uom_ids:
            uom_data.append(
                {'id':uom_id.id,'name':uom_id.name,'type':uom_id.uom_type,'ratio':uom_id.factor_inv}
            )

        return valid_response(data=uom_data)


    @validate_token
    @http.route("/salesperson/partner_ledger", methods=["GET"], type="http", auth="none", csrf=False)
    def get_partner_ledger(self, **kwargs):

        partner_id = int(kwargs.get("partner_id"))
        if not partner_id:
            return invalid_response(
                "Missing Partner  Id.",
            )

        model = 'account.move.line'

        fetch_id = request.env['fetch.data'].sudo().search([("model_id.model", "=", model)], limit=1,order='id desc')

        if not fetch_id:
            return invalid_response(
                "invalid object model", "The model %s is not available in the registry." % model,
            )

        fields = self.get_allowed_fields(fetch_id)
        # domain = ['&','&','&',('posted','=',True),('payable','=',True),('receivable','=',True),('unreconciled','=',True)]
        domain = ['&','&',('partner_id','=',int(partner_id)),('parent_state','=','posted'),('account_id.account_type','in',('asset_receivable','liability_payable'))]

        print(fields)
        try:
            model = request.env[self._model].sudo().search([("model", "=", model)], limit=1,order='id desc')
            if model:
                data = request.env[model.model].sudo().search_read(
                    domain=domain, fields=self.get_allowed_fields(fetch_id),order="id ASC",
                )
                return valid_response(data=data)

        except:

            return invalid_response(
                "Failed",
            )

    @validate_token
    @http.route('/salesperson/new_customer', methods=["post"], type="http", auth="none", csrf=False)
    def create_customer(self, **post):

        params = ["name", "mobile", "phone", "city", "state_id", "street", "comment", "partner_latitude","map_url", "partner_longitude", "date_localization", "user_id"]

        params = {key: post.get(key) for key in params if post.get(key)}
        name, mobile, phone, city, state_id, street, comment, partner_latitude,map_url, partner_longitude, date_localization, user_id = (
            params.get("name"),
            params.get("mobile"),
            params.get("phone"),
            params.get("city"),
            params.get("state_id"),
            params.get("street"),
            params.get("comment"),
            params.get("partner_latitude"),
            params.get("map_url"),
            params.get("partner_longitude"),
            params.get("date_localization"),
            params.get("user_id")

        )
        if not all([name]):
            return invalid_response(
                "missing error", "Name are missing  ", 403,
            )

        date_obj = datetime.strptime(date_localization, '%Y-%m-%d').date()
        try:
            request.env['res.partner'].sudo().create_partner({
                'name': name,
                'mobile': mobile,
                'phone': phone,
                'city': city,
                'state_id': int(state_id),
                'street': street,
                'comment': comment,
                'partner_latitude': partner_latitude,
                'map_url': map_url,
                'partner_longitude': partner_longitude,
                'date_localization': date_obj,
                "user_id": int(user_id),
                "customer_rank": 1,
                "sales_persons_ids":  [(4,int(user_id))],


            })
        except:
            return invalid_response(
                "error", "Partner Not Created", 403,
            )

        return werkzeug.wrappers.Response(
            status=200,
            content_type="application/json; charset=utf-8",
            headers=[("Cache-Control", "no-store"), ("Pragma", "no-cache")],
            response=json.dumps(
                {"status": True,

                 }
            ),
        )

    @validate_token
    @http.route('/salesperson/edit_customer', methods=["post"], type="http", auth="none", csrf=False)
    def edit_customer(self, **post):

        # Check if at least one non-empty field is present in the post data
        if not any(post.get(key) for key in post if post.get(key)):
            return invalid_response(
                "missing error", "At least one non-empty field is missing", 403,
            )

        params = ["name", "mobile", "phone", "city", "state_id", "street", "comment", "partner_latitude","map_url", "partner_longitude", "date_localization", "user_id",
                  "customer_id"]

        params = {key: post.get(key) for key in params if post.get(key)}
        name, mobile, phone, city, state_id, street, comment, partner_latitude,map_url, partner_longitude, date_localization, user_id, customer_id = (
            params.get("name"),
            params.get("mobile"),
            params.get("phone"),
            params.get("city"),
            params.get("state_id"),
            params.get("street"),
            params.get("comment"),
            params.get("partner_latitude"),
            params.get("map_url"),
            params.get("partner_longitude"),
            params.get("date_localization"),
            params.get("user_id"),
            params.get("customer_id")
        )

        date_obj = datetime.strptime(date_localization, '%Y-%m-%d').date()


        partner = request.env['res.partner'].sudo().browse(int(customer_id))
        if partner:
            # Define the fields that can be updated
            allowed_fields = ["name", "mobile", "phone", "city", "state_id", "street", "comment", "partner_latitude","map_url", "partner_longitude", "date_localization",
                              "user_id"]

            # Filter the allowed fields based on the provided parameters
            update_fields = {key: params.get(key) for key in allowed_fields if params.get(key) is not None}

            partner.write(update_fields)
        else:
            return invalid_response(
                "error", "Customer not found", 404,
            )

        return werkzeug.wrappers.Response(
            status=200,
            content_type="application/json; charset=utf-8",
            headers=[("Cache-Control", "no-store"), ("Pragma", "no-cache")],
            response=json.dumps(
                {"status": True}
            ),
        )

    @validate_token
    @http.route('/salesperson/confirm_quotation', methods=["post"], type="http", auth="none", csrf=False)
    def confirm_quotation(self, **kwargs):

        quotation_id = kwargs.get("quotation_id")


        if not quotation_id:
            return invalid_response(
                "Missing quotation  Id.",
            )

        quotation_obj=request.env['sale.order'].sudo().browse(int(quotation_id))
        if quotation_obj.state=='sale' :
            return werkzeug.wrappers.Response(
                status=200,
                content_type="application/json; charset=utf-8",
                headers=[("Cache-Control", "no-store"), ("Pragma", "no-cache")],
                response=json.dumps(
                    {
                        "status": "Already Confirmed",


                    }
                ),
            )
        quotation_obj.action_confirm()
        if quotation_obj.state=='sale' :
            return werkzeug.wrappers.Response(
                status=200,
                content_type="application/json; charset=utf-8",
                headers=[("Cache-Control", "no-store"), ("Pragma", "no-cache")],
                response=json.dumps(
                    {
                        "status": True,


                    }
                ),
            )
        return invalid_response("Not Confirmed")


    @validate_token
    @http.route('/salesperson/register_payment', methods=["post"], type="http", auth="none", csrf=False)
    def register_payment(self, **kwargs):
        invoice_id = int(kwargs.get("invoice_id"))
        journal = int(kwargs.get("journal").strip('"'))
        amount = float(kwargs.get("amount"))
        memo =  kwargs.get("memo")

        if not (invoice_id or journal):
            return invalid_response(
                "Missing invoice | Journal Id.",
            )
        invoice_obj=request.env['account.move'].sudo().browse(int(invoice_id))
        payment = request.env['account.payment'].sudo().create({
            'currency_id': invoice_obj.currency_id.id,
            'amount': amount,
            'payment_type': 'inbound',
            'partner_id': invoice_obj.commercial_partner_id.id,
            'partner_type': 'customer',
            'ref': memo if memo else invoice_obj.payment_reference or invoice_obj.name,
            'journal_id': journal
        })

        payment.action_post()
        line_id = payment.line_ids.filtered(lambda l: l.credit)
        invoice_obj.js_assign_outstanding_line(line_id.id)

        model = 'account.payment'
        fetch_id = request.env['fetch.data'].sudo().search([("model_id.model", "=", model)], limit=1)
        if not fetch_id:
            return invalid_response(
                "invalid object model", "The model %s is not available in the registry." % model,
            )
        field_names = [rec.name for rec in fetch_id.field_ids]
        data = request.env[model].sudo().search_read(domain=[('id', '=', payment.id)],
                                                     fields=field_names, )

        for item in data:
            # Check if the date is a datetime object
            if isinstance(item['date'], datetime):
                item['date'] = item['date'].strftime('%Y-%m-%d')  # Adjust format as needed
            # Check if the date is a date object
            elif isinstance(item['date'], date):  # Correctly check for datetime.date objects
                item['date'] = item['date'].strftime('%Y-%m-%d')


        return werkzeug.wrappers.Response(
            status=200,
            content_type="application/json; charset=utf-8",
            headers=[("Cache-Control", "no-store"), ("Pragma", "no-cache")],
            response=json.dumps(
                {
                    "status": True,
                    "invoice_state": invoice_obj.payment_state,
                    "data": data ,

                }
            ),
        )


    @validate_token
    @http.route('/salesperson/register_payment_customer', methods=["post"], type="http", auth="none", csrf=False)
    def register_payment_customer(self, **kwargs):
        journal = kwargs.get("journal")
        amount = kwargs.get("amount")
        memo = kwargs.get("memo")
        payment_type = kwargs.get("payment_type")
        partner = kwargs.get("partner")
        partner_type = kwargs.get("partner_type")
        confirm_payment = kwargs.get("confirm_payment")


        if not all([journal, payment_type, amount,partner ,partner_type]):
            # Empty 'db' or 'username' or 'password:
            return invalid_response(
                "missing error", "either of the following are missing [journal, payment_type, amount,partner ,partner_type]", 403,
            )
        try:
            payment=request.env['account.payment'].sudo().create({
                'amount': float(amount),
                'payment_type': payment_type,
                'partner_id': int(partner),
                'partner_type': partner_type,
                'journal_id': int(journal),
                'ref':memo,

                })



            if int(confirm_payment)==1:
                payment.action_post()

            model = 'account.payment'
            fetch_id = request.env['fetch.data'].sudo().search([("model_id.model", "=", model)], limit=1)
            if not fetch_id:
                return invalid_response(
                    "invalid object model", "The model %s is not available in the registry." % model,
                )
            field_names = [rec.name for rec in fetch_id.field_ids]
            data = request.env[model].sudo().search_read(domain=[('id', '=', payment.id)],
                                                                   fields=field_names, )

            for item in data:
                # Check if the date is a datetime object
                if isinstance(item['date'], datetime):
                    item['date'] = item['date'].strftime('%Y-%m-%d')  # Adjust format as needed
                # Check if the date is a date object
                elif isinstance(item['date'], date):  # Correctly check for datetime.date objects
                    item['date'] = item['date'].strftime('%Y-%m-%d')

            return werkzeug.wrappers.Response(
                status=200,
                content_type="application/json; charset=utf-8",
                headers=[("Cache-Control", "no-store"), ("Pragma", "no-cache")],
                response=json.dumps(
                    {
                        "status": True,
                         "data": data,

                    }
                ),
            )

        except:
            return invalid_response("Not Created")



    @validate_token
    @http.route('/salesperson/create_order', methods=["post"], type="http", auth="none", csrf=False)
    def create_sale_order(self):

            data = json.loads(request.httprequest.data)
            lines=data.get('sale_order_lines')
            order_lines=[]
            for line in lines:
                order_lines.append(
                    (0, 0, {
                        'product_id': int(line.get('product_id')),
                        'product_uom_qty': line.get('product_uom_qty'),
                        'discount': line.get('discount'),
                        'fixed_discount': line.get('fixed_discount'),
                        'sale_order_note': line.get('sale_order_note'),
                        'product_uom': line.get('product_uom'),

                        # Add other relevant fields
                    })
                )
            global_discount=data.get('global_discount')
            gifts=data.get('gifts')
            if global_discount:
                    order_lines.append(
                        (0, 0, {
                            'product_id': int(global_discount.get('product_id')),
                            'product_uom_qty': 1,
                            'price_unit': - float(global_discount.get('price_unit')),

                        })
                    )
            if gifts:
                for gift in gifts:
                    order_lines.append(
                        (0, 0, {
                            'product_id': int(gift.get('product_id')),
                            'sale_order_note': gift.get('note'),
                             'product_uom_qty': 1,
                            'price_unit': 0.0,

                        })
                    )

            sale_order = request.env['sale.order'].create_order({
                'partner_id': data.get('partner_id'),
                'pricelist_id': data.get('pricelist_id'),
                'user_id': data.get('user_id'),
                'date_order': data.get('date_order'),
                'notes_for_customer': data.get('notes_for_customer'),
                'note': data.get('note'),
                'company_id': request.env['res.users'].sudo().browse(data.get('user_id')).company_id.id,
                'order_line': order_lines,

                # Add other relevant fields
            })

            return werkzeug.wrappers.Response(
                status=200,
                content_type="application/json; charset=utf-8",
                headers=[("Cache-Control", "no-store"), ("Pragma", "no-cache")],
                response=json.dumps(
                    {
                        'id': sale_order.id, 'name': sale_order.get_name()

                    }
                ),
            )

    @validate_token
    @http.route('/salesperson/apply_program', methods=["POST"], type="http", auth="none", csrf=False)
    def apply_program(self, **kwargs):
        sale_id = int(kwargs.get("sale_id"))

        # Validate required parameter
        if not sale_id:
            return werkzeug.wrappers.Response(
                status=400,
                content_type="application/json; charset=utf-8",
                headers=[("Cache-Control", "no-store"), ("Pragma", "no-cache")],
                response=json.dumps({"status": False, "error": "Missing required parameters: sale_id."}),
            )

        # Find the sale.order record
        sale_order = request.env['sale.order'].sudo().browse(sale_id)
        if not sale_order.exists():
            return werkzeug.wrappers.Response(
                status=404,
                content_type="application/json; charset=utf-8",
                headers=[("Cache-Control", "no-store"), ("Pragma", "no-cache")],
                response=json.dumps({"status": False, "error": "Sale order not found."}),
            )

        # Apply the program reward logic
        try:
            sale_order.ensure_one()  # Ensures that we are working with a single sale order record

            # Update programs and rewards
            sale_order._update_programs_and_rewards()

            # Get claimable rewards
            claimable_rewards = sale_order._get_claimable_rewards()

            coupon = next(iter(claimable_rewards ))

            print(coupon)


            # Apply the reward if exactly one coupon and one reward is found
            if coupon:
                sale_order._apply_program_reward(claimable_rewards[coupon], coupon)

                return werkzeug.wrappers.Response(
                        status=200,
                        content_type="application/json; charset=utf-8",
                        headers=[("Cache-Control", "no-store"), ("Pragma", "no-cache")],
                        response=json.dumps(
                            {"status": True, "message": "Program reward applied successfully.", "sale_id": sale_id}),
                    )

            return werkzeug.wrappers.Response(
                status=400,
                content_type="application/json; charset=utf-8",
                headers=[("Cache-Control", "no-store"), ("Pragma", "no-cache")],
                response=json.dumps({"status": False, "error": "No valid rewards  ."}),
            )

        except Exception as e:
            return werkzeug.wrappers.Response(
                status=500,
                content_type="application/json; charset=utf-8",
                headers=[("Cache-Control", "no-store"), ("Pragma", "no-cache")],
                response=json.dumps({"status": False, "error": str(e)}),
            )

    @validate_token
    @http.route('/salesperson/create_visit', methods=["POST"], type="http", auth="none", csrf=False)
    def create_visit(self, **kwargs):
        # Extract parameters from query
        partner_id = int(kwargs.get("partner_id"))
        user_id = int(kwargs.get("user_id"))
        from_time = kwargs.get("from_time").strip('"')
        to_time = kwargs.get("to_time").strip('"')
        notes = kwargs.get("notes", "")

        # Validate required parameters
        if not (partner_id and user_id and from_time and to_time):
            return werkzeug.wrappers.Response(
                status=400,
                content_type="application/json; charset=utf-8",
                headers=[("Cache-Control", "no-store"), ("Pragma", "no-cache")],
                response=json.dumps({"status": False, "error": "Missing required parameters."}),
            )

        try:
            # Create the sales.visit record
            visit = request.env['sales.visit'].sudo().create({
                'partner_id': partner_id,
                'user_id': user_id,
                'from_time': from_time,
                'to_time': to_time,
                'notes': notes,
            })

            # Handling image files from the body
            data_files = request.httprequest.files.getlist('data_files')  # 'data_files' field name in body
            if data_files:
                for file in data_files:
                    filename = secure_filename(file.filename)
                    attachment = request.env['ir.attachment'].sudo().create({
                        'name': filename,
                        'res_model': 'sales.visit',
                        'res_id': visit.id,
                        'type': 'binary',
                        'datas': base64.b64encode(file.read()),  # Encode the image in base64
                        'mimetype': file.content_type,
                    })

                    visit.message_post(body="Attachments", attachment_ids=[attachment.id])

            return werkzeug.wrappers.Response(
                status=200,
                content_type="application/json; charset=utf-8",
                headers=[("Cache-Control", "no-store"), ("Pragma", "no-cache")],
                response=json.dumps({"status": True, "visit_id": visit.id}),
            )

        except Exception as e:
            return werkzeug.wrappers.Response(
                status=500,
                content_type="application/json; charset=utf-8",
                headers=[("Cache-Control", "no-store"), ("Pragma", "no-cache")],
                response=json.dumps({"status": False, "error": str(e)}),
            )
    @validate_token
    @http.route('/salesperson/update_visit', methods=["POST"], type="http", auth="none", csrf=False)
    def update_visit(self, **kwargs):
        visit_id = int(kwargs.get("visit_id"))
        partner_id = int(kwargs.get("partner_id"))
        user_id = int(kwargs.get("user_id"))
        from_time = kwargs.get("from_time").strip('"')
        to_time = kwargs.get("to_time").strip('"')
        notes = kwargs.get("notes", "")

        # Validate required parameters
        if not (visit_id and partner_id and user_id and from_time and to_time):
            return werkzeug.wrappers.Response(
                status=400,
                content_type="application/json; charset=utf-8",
                headers=[("Cache-Control", "no-store"), ("Pragma", "no-cache")],
                response=json.dumps({"status": False, "error": "Missing required parameters."}),
            )

        # Find the existing sales.visit record
        visit = request.env['sales.visit'].sudo().browse(visit_id)
        if not visit:
            return werkzeug.wrappers.Response(
                status=404,
                content_type="application/json; charset=utf-8",
                headers=[("Cache-Control", "no-store"), ("Pragma", "no-cache")],
                response=json.dumps({"status": False, "error": "Visit not found."}),
            )

        # Update the sales.visit record
        try:
            visit.write({
                'partner_id': partner_id,
                'user_id': user_id,
                'from_time': from_time,
                'to_time': to_time,
                'notes': notes,
            })


            # Handling image files from the body
            data_files = request.httprequest.files.getlist('data_files')  # 'data_files' field name in body
            if data_files:
                for file in data_files:
                    filename = secure_filename(file.filename)
                    attachment = request.env['ir.attachment'].sudo().create({
                        'name': filename,
                        'res_model': 'sales.visit',
                        'res_id': visit.id,
                        'type': 'binary',
                        'datas': base64.b64encode(file.read()),  # Encode the image in base64
                        'mimetype': file.content_type,
                    })

                    visit.message_post(body="Attachments", attachment_ids=[attachment.id])




            return werkzeug.wrappers.Response(
                status=200,
                content_type="application/json; charset=utf-8",
                headers=[("Cache-Control", "no-store"), ("Pragma", "no-cache")],
                response=json.dumps({"status": True, "visit_id": visit.id}),
            )

        except Exception as e:
            return werkzeug.wrappers.Response(
                status=500,
                content_type="application/json; charset=utf-8",
                headers=[("Cache-Control", "no-store"), ("Pragma", "no-cache")],
                response=json.dumps({"status": False, "error": str(e)}),
            )

    @validate_token
    @http.route('/salesperson/create_invoice', methods=["post"], type="http", auth="none", csrf=False)
    def create_invoice(self):
            invoice_lines = json.loads(request.httprequest.data)
            data=invoice_lines.get('invoice_lines')
            lines=[]
            for line in data:
                lines.append(
                    (0, 0, {
                        'product_id': line.get('product_id'),
                        'quantity': line.get('quantity'),
                        'price_unit': line.get('price_unit'),
                        # Add other relevant fields
                    })
                )

            invoice = request.env['account.move'].create_invoice({
                'partner_id': invoice_lines.get('partner_id'),
                'invoice_date': invoice_lines.get('date'),
                'move_type': "out_invoice",
                'invoice_line_ids': lines,
                # Add other relevant fields
            })


            return werkzeug.wrappers.Response(
                status=200,
                content_type="application/json; charset=utf-8",
                headers=[("Cache-Control", "no-store"), ("Pragma", "no-cache")],
                response=json.dumps(
                    {
                        'success': True, 'invoice_id': invoice.id

                    }
                ),
            )


    @validate_token
    @http.route('/salesperson/create_order_invoice', methods=["post"], type="http", auth="none", csrf=False)
    def create_order_invoice(self, **kwargs):
        order_id = kwargs.get("order_id")

        if not order_id:
            return invalid_response(
                "Missing Order Id.",
            )

        order = request.env['sale.order'].sudo().browse(int(order_id))
        order.sudo()._create_invoices()

        return werkzeug.wrappers.Response(
            status=200,
            content_type="application/json; charset=utf-8",
            headers=[("Cache-Control", "no-store"), ("Pragma", "no-cache")],
            response=json.dumps(
                {
                    "status": True,

                }
            ),
        )


