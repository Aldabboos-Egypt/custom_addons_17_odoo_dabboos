import ast
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

_logger = logging.getLogger(__name__)


def validate_token(func):
    """."""


    @functools.wraps(func)
    def wrap(self, *args, **kwargs):
        """."""
        access_token = request.httprequest.headers.get("access_token")
        if not access_token:
            return invalid_response("access_token_not_found", "missing access token in request header", 401)
        access_token_data = (
            request.env["api.access_token"].sudo().search([("token", "=", access_token)], order="id DESC", limit=1)
        )

        if access_token_data.find_one_or_create_token(user_id=access_token_data.user_id.id) != access_token:
            return invalid_response("access_token", "token seems to have expired or invalid", 401)

        # request.session.uid = access_token_data.user_id.id
        request.session.update({
            'uid': access_token_data.user_id.id,
        })

        uid = int(access_token_data.user_id.id)  # 0 is a default value if 'id' is not present
        request.update_env(uid)
        # request.uid = access_token_data.user_id.id
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
    def get(self,):
        model = request.httprequest.headers.get("model")
        domain_fields_dict = request.httprequest.headers.get("domain")
        fetch_id = request.env['fetch.data'].search([("model_id.model", "=", model)], limit=1)

        if not fetch_id:
            return invalid_response(
                "invalid object model", "The model %s is not available in the registry." % model,
            )
        domain = []

        if domain_fields_dict:
            domain_fields_dict = ast.literal_eval(domain_fields_dict)
            domain_fields_keys = list(domain_fields_dict.keys())
            for rec in range(0, len(domain_fields_keys) - 1):
                domain += ['|']
            for key in domain_fields_keys:
                if type(domain_fields_dict.get(key)) is list:
                    domain += [(key, 'in', domain_fields_dict.get(key))]

                elif isinstance(domain_fields_dict.get(key), int):
                    domain += [(key, '=', domain_fields_dict.get(key))]

                else:
                    domain += [(key, 'ilike', domain_fields_dict.get(key))]

        try:
            ioc_name = model
            model = request.env[self._model].search([("model", "=", model)], limit=1, order='id desc')
            if model:
                print(domain)

                # domain, fields, offset, limit, order = extract_arguments(**payload)
                data = request.env[model.model].search_read(
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

            return invalid_response("Access error", "Error: %s" % e.name)

    @validate_token
    @http.route("/salesperson/get_products_categories", methods=["GET"], type="http", auth="none", csrf=False)
    def get_products_categories(self):
        category_id = int(request.httprequest.headers.get("category_id"))
        pricelist_id = int(request.httprequest.headers.get("pricelist_id"))
        user_id = int(request.httprequest.headers.get("user_id"))

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

        category_id_object = request.env['product.category'].browse(int(category_id))

        if category_id_object.child_id:
            all_child_ids = get_all_child_ids(category_id_object)
            domain = ['|', ('categ_id', '=', int(category_id)), ('categ_id', 'in', all_child_ids)]
        else:
            domain = [('categ_id', '=', int(category_id))]

        pricelist_id = int(request.httprequest.headers.get("pricelist_id"))
        pricelist = request.env['product.pricelist'].browse(pricelist_id)
        if not pricelist:
            return invalid_response(
                "Pricelist Not Found", 403,
            )
        product_ids = request.env['product.product'].search(domain)
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

        location_ids = request.env['res.users'].browse(user_id).allowed_locations

        print(len(all_product_list))

        quants = request.env['stock.quant'].search([
            ('location_id', 'in', location_ids.ids), ('product_id', '=', product_ids.ids)
        ])

        # Create a dictionary to store product quantities
        quantities = {}

        # Iterate through quants and update the quantities dictionary
        for quant in quants:
            print(quant)
            if quant.product_id.id not in quantities:
                quantities[quant.product_id.id] = quant.available_quantity
            else:
                quantities[quant.product_id.id] += quant.available_quantity

        print(all_product_list)
        print(quantities)
        for item in all_product_list:
            item['QTY_1'] = quantities.get(item.get('ID_1'), 0)

        print(all_product_list)
        d2 = all_product_list

        model = 'product.product'
        fetch_id = request.env['fetch.data'].search([("model_id.model", "=", model)], limit=1)
        if not fetch_id:
            return invalid_response(
                "invalid object model", "The model %s is not available in the registry." % model,
            )
        field_names = [rec.name for rec in fetch_id.field_ids]
        d1 = request.env['product.product'].search_read(domain=[('id', 'in', product_ids.ids)], fields=field_names, )

        d1_dict = {item['id']: item for item in d1}

        # Merge d2 into d1 based on 'id'
        merged_data = []
        for item_d2 in d2:
            id_d2 = item_d2.get('ID_1')
            if id_d2 in d1_dict:
                item_d1 = d1_dict[id_d2]
                item_d1.update(item_d2)  # Merge the dictionaries
                merged_data.append(item_d1)

        print(merged_data)

        return valid_response(data=merged_data)

    @validate_token
    @http.route("/salesperson/product_price", methods=["GET"], type="http", auth="none", csrf=False)
    def get_product_price(self):
        pricelist_id = int(request.httprequest.headers.get("pricelist_id"))
        user_id = int(request.httprequest.headers.get("user_id"))

        data_input = all([pricelist_id, user_id])
        if not data_input:
            # Empty 'db' or 'username' or 'password:
            return invalid_response(
                "missing error", "either of the following are missing [category_id, pricelist_id,user_id]", 403,
            )

        pricelist_id = int(request.httprequest.headers.get("pricelist_id"))
        pricelist = request.env['product.pricelist'].browse(pricelist_id)
        if not pricelist:
            return invalid_response(
                "Pricelist Not Found", 403,
            )
        product_ids = request.env['product.product'].search([])
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

        location_ids = request.env['res.users'].browse(user_id).allowed_locations

        print(location_ids)

        quants = request.env['stock.quant'].search([
            ('location_id', 'in', location_ids.ids), ('product_id', '=', product_ids.ids)
        ])

        # Create a dictionary to store product quantities
        quantities = {}

        # Iterate through quants and update the quantities dictionary
        for quant in quants:
            print(quant)
            if quant.product_id.id not in quantities:
                quantities[quant.product_id.id] = quant.available_quantity
            else:
                quantities[quant.product_id.id] += quant.available_quantity

        print(all_product_list)
        print(quantities)
        for item in all_product_list:
            item['QTY_1'] = quantities.get(item.get('ID_1'), 0)

        print(all_product_list)
        d2 = all_product_list

        model = 'product.product'
        fetch_id = request.env['fetch.data'].search([("model_id.model", "=", model)], limit=1)
        if not fetch_id:
            return invalid_response(
                "invalid object model", "The model %s is not available in the registry." % model,
            )
        field_names = [rec.name for rec in fetch_id.field_ids]
        d1 = request.env['product.product'].search_read(domain=[('id', 'in', product_ids.ids)], fields=field_names, )

        d1_dict = {item['id']: item for item in d1}

        # Merge d2 into d1 based on 'id'
        merged_data = []
        for item_d2 in d2:
            id_d2 = item_d2.get('ID_1')
            if id_d2 in d1_dict:
                item_d1 = d1_dict[id_d2]
                item_d1.update(item_d2)  # Merge the dictionaries
                merged_data.append(item_d1)

        print(merged_data)

        return valid_response(data=merged_data)

    @validate_token
    @http.route("/salesperson/get_product_uoms", methods=["GET"], type="http", auth="none", csrf=False)
    def get_product_uoms(self  ):
        product_id = int(request.httprequest.headers.get("product_id"))

        if not product_id:
            return invalid_response(
                "Missing Product Id.",
            )


        product_id=request.env['product.product'].browse(product_id)
        print(product_id)
        if not product_id:
            return invalid_response(
                "  Product Id Not Found.",
            )
        domain = [('category_id', '=', product_id.uom_id.category_id.id)]
        uom_ids=request.env['uom.uom'].search(domain)

        uom_data=[]
        for uom_id in uom_ids:
            uom_data.append(
                {'id':uom_id.id,'name':uom_id.name,'type':uom_id.uom_type,'ratio':uom_id.factor_inv}
            )

        return valid_response(data=uom_data)


    @validate_token
    @http.route("/salesperson/partner_ledger", methods=["GET"], type="http", auth="none", csrf=False)
    def get_partner_ledger(self):
        partner_id = request.httprequest.headers.get("partner_id")

        if not partner_id:
            return invalid_response(
                "Missing Partner  Id.",
            )

        model = 'account.move.line'

        fetch_id = request.env['fetch.data'].search([("model_id.model", "=", model)], limit=1,order='id desc')

        if not fetch_id:
            return invalid_response(
                "invalid object model", "The model %s is not available in the registry." % model,
            )

        fields = self.get_allowed_fields(fetch_id)
        # domain = ['&','&','&',('posted','=',True),('payable','=',True),('receivable','=',True),('unreconciled','=',True)]
        domain = ['&','&',('partner_id','=',int(partner_id)),('parent_state','=','posted'),('account_id.account_type','in',('asset_receivable','liability_payable'))]

        print(fields)
        try:
            model = request.env[self._model].search([("model", "=", model)], limit=1,order='id desc')
            if model:
                data = request.env[model.model].search_read(
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

        params = ["name", "mobile", "phone", "city", "state_id", "street", "comment", "partner_latitude", "partner_longitude", "date_localization", "user_id"]

        params = {key: post.get(key) for key in params if post.get(key)}
        name, mobile, phone, city, state_id, street, comment, partner_latitude, partner_longitude, date_localization, user_id = (
            params.get("name"),
            params.get("mobile"),
            params.get("phone"),
            params.get("city"),
            params.get("state_id"),
            params.get("street"),
            params.get("comment"),
            params.get("partner_latitude"),
            params.get("partner_longitude"),
            params.get("date_localization"),
            params.get("user_id")

        )
        if not all([name]):
            return invalid_response(
                "missing error", "Name   are missing  ", 403,
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
                'partner_longitude': partner_longitude,
                'date_localization': date_obj,
                "user_id": int(user_id)

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

        params = ["name", "mobile", "phone", "city", "state_id", "street", "comment", "partner_latitude", "partner_longitude", "date_localization", "user_id",
                  "customer_id"]

        params = {key: post.get(key) for key in params if post.get(key)}
        name, mobile, phone, city, state_id, street, comment, partner_latitude, partner_longitude, date_localization, user_id, customer_id = (
            params.get("name"),
            params.get("mobile"),
            params.get("phone"),
            params.get("city"),
            params.get("state_id"),
            params.get("street"),
            params.get("comment"),
            params.get("partner_latitude"),
            params.get("partner_longitude"),
            params.get("date_localization"),
            params.get("user_id"),
            params.get("customer_id")
        )

        date_obj = datetime.strptime(date_localization, '%Y-%m-%d').date()

        print(customer_id)

        partner = request.env['res.partner'].sudo().browse(int(customer_id))
        print(partner)
        if partner:
            # Define the fields that can be updated
            allowed_fields = ["name", "mobile", "phone", "city", "state_id", "street", "comment", "partner_latitude", "partner_longitude", "date_localization",
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
    def confirm_quotation(self, **post):

        quotation_id = request.httprequest.headers.get("quotation_id")
        if not quotation_id:
            return invalid_response(
                "Missing quotation  Id.",
            )

        quotation_obj=request.env['sale.order'].browse(int(quotation_id))

        try:
            quotation_obj.action_confirm()
        except:
            return invalid_response()





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


    @validate_token
    @http.route('/salesperson/register_payment', methods=["post"], type="json", auth="none", csrf=False)
    def register_payment(self, **post):
        data = json.loads(request.httprequest.data)
        payment_details = data.get('data')
        invoice_id = payment_details.get("invoice_id")
        journal = int(payment_details.get("journal"))
        memo = payment_details.get("memo")
        amount = payment_details.get("amount")

        # print(max(ssssssssssssss))
        if not (invoice_id or journal):
            return invalid_response(
                "Missing invoice | Journal Id.",
            )
        invoice_obj=request.env['account.move'].browse(int(invoice_id))
        # print("fddddddddddddddd")
        #
        # if float(amount) >invoice_obj.amount_residual:
        #     return invalid_response(
        #         "Amount Is Greater Than Invoice Amount Residual  .",
        #     )
        # print("SSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSs")

        # payment_journal =request.env['account.journal'].search([('api_payment','=',True)],limit=1)
        # payment_method =request.env['account.payment.method'].search([('api_payment','=',True)],limit=1)

        # try:
        payment = request.env['account.payment'].create({
            'currency_id': invoice_obj.currency_id.id,
            'amount': amount,
            'payment_type': 'inbound',
            'partner_id': invoice_obj.commercial_partner_id.id,
            'partner_type': 'customer',
            'ref': memo if memo else invoice_obj.payment_reference or invoice_obj.name,
            # 'payment_method_id': 1,
            'journal_id': journal
        })

        print(payment)


        payment.action_post()
        line_id = payment.line_ids.filtered(lambda l: l.credit)
        invoice_obj.js_assign_outstanding_line(line_id.id)
        return   {
                    "status": True,
                    "invoice_sate": invoice_obj.payment_state,


                }

        # except:
        #     return invalid_response(
        #         "No Payment Done", 404,
        #     )


    @validate_token
    @http.route('/salesperson/register_payment_customer', methods=["post"], type="json", auth="none", csrf=False)
    def register_payment_customer(self, **post):
        data = json.loads(request.httprequest.data)
        payment_details = data.get('data')
        journal = payment_details.get("journal")
        payment_type = payment_details.get("payment_type")
        amount = payment_details.get("amount")
        partner = payment_details.get("partner")
        memo = payment_details.get("memo")
        partner_type = payment_details.get("partner_type")
        confirm_payment = payment_details.get("confirm_payment")

        if not all([journal, payment_type, amount,partner ,partner_type]):
            # Empty 'db' or 'username' or 'password:
            return invalid_response(
                "missing error", "either of the following are missing [journal, payment_type, amount,partner ,partner_type]", 403,
            )


        try:
            payment=request.env['account.payment'].create({
                'amount': float(amount),
                'payment_type': payment_type,
                'partner_id': int(partner),
                'partner_type': partner_type,
                'journal_id': int(journal),
                'ref':memo,

            })

            if int(confirm_payment)==1:
                payment.action_post()

            return  {
                        "status": True,


                    }

        except:
            return invalid_response(
                "No Payment Done", 404,
            )


    @validate_token
    @http.route('/salesperson/create_order', methods=["post"], type="json", auth="none", csrf=False)
    def create_sale_order(self, **kwargs):
            try:
                # Extract the list of dictionaries from the request body
                sale_order_lines = json.loads(request.httprequest.data)


                # Ensure that the data is in the correct format
                # if not isinstance(sale_order_lines, list):
                #     return {'error': 'Invalid input format. Expected a list of dictionaries.'}

                # Create the sale order and sale order lines

                data=sale_order_lines.get('sale_order_lines')
                order_lines=[]
                for line in data:
                    order_lines.append(
                        (0, 0, {
                            'product_id': line.get('product_id'),
                            'product_uom_qty': line.get('product_uom_qty'),
                            'discount': line.get('discount'),
                            'fixed_discount': line.get('fixed_discount'),
                            'sale_order_note': line.get('sale_order_note'),
                            'product_uom': line.get('product_uom'),

                            # Add other relevant fields
                        })
                    )

                sale_order = request.env['sale.order'].create_order({
                    'partner_id': sale_order_lines.get('partner_id'),
                    'user_id': sale_order_lines.get('user_id'),

                    'date_order': sale_order_lines.get('date_order'),
                    'note': sale_order_lines.get('extra_notes'),
                    'order_line': order_lines,

                    # Add other relevant fields
                })






                return { 'id': sale_order.id , 'name':sale_order.get_name()}

            except Exception as e:
                return {'error': str(e)}

    @validate_token
    @http.route('/salesperson/create_invoice', methods=["post"], type="json", auth="none", csrf=False)
    def create_invoice(self, **kwargs):

            print("eeeeeeeeeeee")
            try:
                # Extract the list of dictionaries from the request body
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





                return {'success': True, 'invoice_id': invoice.id}

            except Exception as e:
                return {'error': str(e)}


    @validate_token
    @http.route('/salesperson/create_order_invoice', methods=["post"], type="http", auth="none", csrf=False)

    def create_order_invoice(self, **kwargs):

        order_id = request.httprequest.headers.get("order_id")
        if not order_id:
            return invalid_response(
                "Missing Order Id.",
            )

        try:

            order = request.env['sale.order'].browse(int(order_id))
            order._create_invoices()

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

        except :
            return invalid_response(
                "Invoice Not Created", 404,
            )


    @validate_token
    @http.route(_routes, type="http", auth="none", methods=["POST"], csrf=False)
    def post(self, model=None, id=None, **payload):

        payload = request.httprequest.data.decode()
        fetch_id = request.env['fetch.data'].search([("model_id.model", "=", model)], limit=1)
        print(fetch_id)
        if not fetch_id:
            return invalid_response(
                "invalid object model", "The model %s is not available in the registry." % model,
            )

        # user = request.env['res.users'].sudo().create_partner({
        #     'name': name,
        #     'login': login,
        #     'phone': mobile,
        #     'password': password,
        #     'state_id': governerateid,
        #     'city_id': cityid,
        # })


        object = request.env[model].sudo().create(payload)

        print(object)

        data = object.read(fields=object)
        if object:
            return valid_response(object)
        else:
            return valid_response(data)

    @validate_token
    @http.route(_routes, type="http", auth="none", methods=["PUT"], csrf=False)
    def put(self, model=None, id=None, **payload):
        """."""
        values = {}
        payload = request.httprequest.data.decode()
        payload = json.loads(payload)
        try:
            _id = int(id)
        except Exception as e:
            return invalid_response("invalid object id", "invalid literal %s for id with base " % id)
        _model = request.env[self._model].sudo().search([("model", "=", model)], limit=1)
        if not _model:
            return invalid_response(
                "invalid object model", "The model %s is not available in the registry." % model, 404,
            )
        try:
            record = request.env[_model.model].sudo().browse(_id)
            for k, v in payload.items():
                if "__api__" in k:
                    values[k[7:]] = ast.literal_eval(v)
                else:
                    values[k] = v
            record.write(values)
        except Exception as e:
            request.env.cr.rollback()
            return invalid_response("exception", e)
        else:
            return valid_response(record.read())

    @validate_token
    @http.route(_routes, type="http", auth="none", methods=["DELETE"], csrf=False)
    def delete(self, model=None, id=None, **payload):
        """."""
        try:
            _id = int(id)
        except Exception as e:
            return invalid_response("invalid object id", "invalid literal %s for id with base " % id)
        try:
            record = request.env[model].sudo().search([("id", "=", _id)])
            if record:
                record.unlink()
            else:
                return invalid_response("missing_record", "record object with id %s could not be found" % _id, 404,)
        except Exception as e:
            request.env.cr.rollback()
            return invalid_response("exception", e.name, 503)
        else:
            return valid_response("record %s has been successfully deleted" % record.id)

    @validate_token
    @http.route(_routes, type="http", auth="none", methods=["PATCH"], csrf=False)
    def patch(self, model=None, id=None, action=None, **payload):
        """."""
        args = []

        payload = request.httprequest.data.decode()
        args = ast.literal_eval(payload)
        try:
            _id = int(id)
        except Exception as e:
            return invalid_response("invalid object id", "invalid literal %s for id with base" % id)
        try:
            record = request.env[model].sudo().search([("id", "=", _id)], limit=1)
            _callable = action in [method for method in dir(record) if callable(getattr(record, method))]
            if record and _callable:
                # action is a dynamic variable.
                res = getattr(record, action)(*args) if args else getattr(record, action)()
            else:
                return invalid_response(
                    "invalid object or method",
                    "The given action '%s ' cannot be performed on record with id '%s' because '%s' has no such method"
                    % (action, _id, model),
                    404,
                )
        except Exception as e:
            return invalid_response("exception", e, 503)
        else:
            return valid_response(res)
