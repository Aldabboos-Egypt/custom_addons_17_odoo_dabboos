import ast
import base64
import functools
import json
import logging
from datetime import datetime
import pytz
import werkzeug.wrappers
import json
import base64

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
        company_domain = kwargs.get("company_domain")
        print(category_id,pricelist_id,user_id)
        data_input = all([category_id, pricelist_id, user_id])
        domain=[]
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


        if company_domain  :
            domain += ast.literal_eval(company_domain)


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
        company_domain = kwargs.get("company_domain")
        domain=[]
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

        if company_domain  :
            domain = ast.literal_eval(company_domain)


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
    @http.route('/salesperson/new_customer', methods=["POST"], type="http", auth="none", csrf=False)
    def create_customer(self, **post):

        # Ensure all fields are retrieved
        params = {
            "name": post.get("name"),
            "mobile": post.get("mobile"),
            "phone": post.get("phone"),
            "city": post.get("city"),
            "state_id": post.get("state_id"),
            "street": post.get("street"),
            "comment": post.get("description"),
            "partner_latitude": post.get("partner_latitude"),
            "partner_longitude": post.get("partner_longitude"),
            "map_url": post.get("map_url"),
            "date_localization": post.get("date"),
            "user_id": post.get("user_id"),
            "sales_person_ids": post.get("sales_persons_ids"),
        }

        print("Received Data:", params)  # Debugging

        # Ensure required field `name` is present
        if not params["name"]:
            return invalid_response("missing_error", "Name is required", 403)

        # Convert date
        date_obj = None
        if params["date_localization"]:
            try:
                date_obj = datetime.strptime(params["date_localization"], '%Y-%m-%d').date()
            except ValueError:
                return invalid_response("format_error", "Invalid date format", 400)

        # Process profile picture
        profile_picture = request.httprequest.files.get('profile_picture')
        image_data = base64.b64encode(profile_picture.read()).decode('utf-8') if profile_picture else None

        # Convert state_id to valid integer
        state_id = request.env['res.country.state'].sudo().search([('name', '=', params["state_id"])],
                                                                  limit=1).id or False

        # Convert user_id to integer
        user_id = int(params["user_id"]) if params["user_id"] and params["user_id"].isdigit() else False

        # Ensure sales_person_ids are properly parsed
        sales_persons_ids = params["sales_person_ids"]
        print(f"Raw sales_person_ids: {sales_persons_ids}")  # Debugging

        if sales_persons_ids:
            try:
                cleaned_ids = json.loads(sales_persons_ids) if sales_persons_ids.startswith('"') else sales_persons_ids
                sales_persons_list = [int(uid) for uid in cleaned_ids.split(",") if uid.strip().isdigit()]
            except json.JSONDecodeError:
                sales_persons_list = [int(uid) for uid in sales_persons_ids.split(",") if uid.strip().isdigit()]
        else:
            sales_persons_list = []

        print("Sales Persons List:", sales_persons_list)  # Debugging

        # Validate sales_person_ids exist
        valid_users = request.env['res.users'].sudo().browse(sales_persons_list)
        valid_user_ids = valid_users.ids if valid_users else []

        print("Valid Users:", valid_user_ids)  # Debugging

        # Create customer
        partner = request.env['res.partner'].sudo().create({
            'name': params["name"],
            'mobile': params["mobile"],
            'phone': params["phone"],
            'city': params["city"],
            'state_id': state_id or False,
            'street': params["street"],
            'comment': params["comment"],
            'partner_latitude': params["partner_latitude"],
            'partner_longitude': params["partner_longitude"],
            'map_url': params["map_url"],
            'date_localization': date_obj,
            'user_id': user_id,
            'customer_rank': 1,
            'image_1920': image_data,
        })

        # Assign salespersons if valid
        if valid_user_ids:
            partner.sudo().write({'sales_persons_ids': [(6, 0, valid_user_ids)]})

        print("Updated Sales Persons:", partner.sales_persons_ids.ids)  # Debugging



        return valid_response({"status": True, "partner_id": partner.id})


    @validate_token
    @http.route('/salesperson/edit_customer', methods=["POST"], type="http", auth="none", csrf=False)
    def edit_customer(self, **post):
        customer_id = post.get("customer_id")

        # Validate customer_id
        if not customer_id or not customer_id.isdigit():
            return invalid_response("missing_error", "Valid Customer ID is required", 403)

        partner = request.env['res.partner'].sudo().browse(int(customer_id))
        if not partner.exists():
            return invalid_response("error", "Customer not found", 404)

        allowed_fields = ["name", "mobile", "phone", "city", "state_id", "street", "comment",
                          "partner_latitude", "map_url", "partner_longitude", "date_localization", "user_id"]
        update_fields = {key: post.get(key) for key in allowed_fields if post.get(key)}

        try:
            # Debugging: Print received fields
            print(f"Received Update Fields: {update_fields}")

            # Handle profile picture update
            profile_picture = request.httprequest.files.get('profile_picture')
            if profile_picture:
                update_fields['image_1920'] = base64.b64encode(profile_picture.read()).decode('utf-8')

            # Handle date_localization conversion
            if "date_localization" in update_fields:
                try:
                    update_fields['date_localization'] = datetime.strptime(update_fields['date_localization'],
                                                                           '%Y-%m-%d').date()
                except ValueError:
                    return invalid_response("format_error", "Invalid date format", 400)

            # Handle state_id conversion
            if "state_id" in update_fields:
                state_id = request.env['res.country.state'].sudo().search([('name', '=', update_fields["state_id"])],
                                                                          limit=1).id or False
                update_fields["state_id"] = state_id

            # Handle user_id conversion
            user_id = post.get("user_id")
            update_fields["user_id"] = int(user_id) if user_id and user_id.isdigit() else False

            # Handle sales_persons_ids (if provided)
            sales_persons_ids = post.get("sales_persons_ids")
            if sales_persons_ids:
                try:
                    cleaned_ids = json.loads(sales_persons_ids) if sales_persons_ids.startswith(
                        '"') else sales_persons_ids
                    sales_persons_list = [int(uid) for uid in cleaned_ids.split(",") if uid.strip().isdigit()]
                except json.JSONDecodeError:
                    sales_persons_list = [int(uid) for uid in sales_persons_ids.split(",") if uid.strip().isdigit()]

                # Validate if users exist
                valid_users = request.env['res.users'].sudo().browse(sales_persons_list)
                valid_user_ids = valid_users.ids if valid_users else []
                update_fields["sales_persons_ids"] = [(6, 0, valid_user_ids)]

                print(f"Valid Sales Persons: {valid_user_ids}")  # Debugging

            # Update partner record
            partner.sudo().write(update_fields)

            print(f"Updated Customer ID {partner.id} Successfully!")  # Debugging
            return valid_response({"status": True, "partner_id": partner.id})

        except Exception as e:
            return invalid_response("error", f"Customer not updated. Reason: {str(e)}", 403)

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
    @http.route('/salesperson/confirm_invoice', methods=["POST"], type="http", auth="none", csrf=False)
    def confirm_invoice(self, **kwargs):
        invoice_id = kwargs.get("invoice_id")

        # Validate the input
        if not invoice_id:
            return invalid_response("Missing invoice ID.")

        try:
            invoice_obj = request.env['account.move'].sudo().browse(int(invoice_id))
            if not invoice_obj or invoice_obj.move_type != 'out_invoice':
                return invalid_response("Invalid or non-existent invoice ID.")

            if invoice_obj.state == 'posted':
                return werkzeug.wrappers.Response(
                    status=200,
                    content_type="application/json; charset=utf-8",
                    headers=[("Cache-Control", "no-store"), ("Pragma", "no-cache")],
                    response=json.dumps({"status": "Already Confirmed"}),
                )

            # Confirm the invoice
            invoice_obj.action_post()
            if invoice_obj.state == 'posted':
                return werkzeug.wrappers.Response(
                    status=200,
                    content_type="application/json; charset=utf-8",
                    headers=[("Cache-Control", "no-store"), ("Pragma", "no-cache")],
                    response=json.dumps({"status": True}),
                )
            return invalid_response("Invoice confirmation failed.")
        except Exception as e:
            return invalid_response(f"An error occurred: {str(e)}")

    @validate_token
    @http.route('/salesperson/register_payment', methods=["post"], type="http", auth="none", csrf=False)
    def register_payment(self, **kwargs):
        invoice_id = int(kwargs.get("invoice_id"))
        journal = int(kwargs.get("journal"))
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


        # data['status']=True
        # data['invoice_state']=invoice_obj.payment_state
        #

        return valid_response(data=data)
        # return werkzeug.wrappers.Response(
        #     status=200,
        #     content_type="application/json; charset=utf-8",
        #     headers=[("Cache-Control", "no-store"), ("Pragma", "no-cache")],
        #     response=json.dumps(
        #         {
        #             "status": True,
        #             "invoice_state": invoice_obj.payment_state,
        #             "data": data ,
        #
        #         }
        #     ),
        # )


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

            # return werkzeug.wrappers.Response(
            #     status=200,
            #     content_type="application/json; charset=utf-8",
            #     headers=[("Cache-Control", "no-store"), ("Pragma", "no-cache")],
            #     response=json.dumps(
            #         {
            #             "status": True,
            #              "data": data,
            #
            #         }
            #     ),
            # )
            return valid_response(data=data)


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
                        'notes_for_us': line.get('notes_for_us'),
                        'notes_for_customer': line.get('notes_for_customer'),

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
                            'notes_for_us': gift.get('notes_for_us'),
                            'notes_for_customer': gift.get('notes_for_customer'),

                             'product_uom_qty': 1,
                            'price_unit': 0.0,

                        })
                    )

            sale_order = request.env['sale.order'].create_order({
                'partner_id': data.get('partner_id'),
                'pricelist_id': data.get('pricelist_id'),
                'user_id': data.get('user_id'),
                'date_order': data.get('date_order'),
                'notes_for_us': data.get('notes_for_us'),
                'notes_for_customer': data.get('notes_for_customer'),
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


        visit = request.env['sales.visit'].sudo().create({
            'partner_id': partner_id,
            'user_id': user_id,
            'from_time': from_time,
            'to_time': to_time,
        'from_time_str': str(from_time),
        'to_time_str': str(to_time),
            'notes': notes,
        })
        data_files = request.httprequest.files.getlist('data_files')  # 'data_files' field name in body

        print(data_files)


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

                print(attachment)
                print(visit)
                print(visit.id)


                visit.message_post(body="Attachments", attachment_ids=[attachment.id])




        return werkzeug.wrappers.Response(
            status=200,
            content_type="application/json; charset=utf-8",
            headers=[("Cache-Control", "no-store"), ("Pragma", "no-cache")],
            response=json.dumps({"status": True, "visit_id": visit.id}),
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


        visit.write({
            'partner_id': partner_id,
            'user_id': user_id,
            'from_time': from_time,
            'to_time': to_time,
            'from_time_str': str(from_time),
            'to_time_str': str(to_time),
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


