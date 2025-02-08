import json
import logging

import werkzeug.wrappers

from odoo import http
from odoo.addons.dabbos_restapi.common import invalid_response, valid_response
from odoo.exceptions import AccessDenied, AccessError
from odoo.http import request

_logger = logging.getLogger(__name__)


class AccessToken(http.Controller):
    """."""


    def verify_token(self, token):

        print(">D>D>", token)
        record = request.env['api.access_token'].sudo().search([
            ('token', '=', token)
        ])

        if len(record) != 1:
            return False


        return record.user_id

    # @http.route("/salesperson/login", methods=["GET"], type="http", auth="none", csrf=False)
    # @http.route('/salesperson/login', methods=["GET"], type="http", auth="none", csrf=False)
    # def login(self, **post):
    #
    #     print('ssssssssssssssssssssssssssddddddddddddddd')
    #
    #     _token = request.env["api.access_token"]
    #     params = ["db", "login", "password"]
    #     params = {key: post.get(key) for key in params if post.get(key)}
    #     db, username, password = (
    #         params.get("db"),
    #         post.get("login"),
    #         post.get("password"),
    #     )
    #     _credentials_includes_in_body = all([db, username, password])
    #     if not _credentials_includes_in_body:
    #         # The request post body is empty the credetials maybe passed via the headers.
    #         headers = request.httprequest.headers
    #         db = headers.get("db")
    #         username = headers.get("login")
    #         password = headers.get("password")
    #         _credentials_includes_in_headers = all([db, username, password])
    #         if not _credentials_includes_in_headers:
    #             # Empty 'db' or 'username' or 'password:
    #             return invalid_response(
    #                 "missing error", "either of the following are missing [db, username,password]", 403,
    #             )
    #     # Login in odoo database:
    #     try:
    #         request.session.authenticate(db, username, password)
    #     except AccessError as aee:
    #         return invalid_response("Access error", "Error: %s" % aee.name)
    #     except AccessDenied as ade:
    #         return invalid_response("Access denied", "Login, password or db invalid")
    #     except Exception as e:
    #         # Invalid database:
    #         info = "The database name is not valid {}".format((e))
    #         error = "invalid_database"
    #         _logger.error(info)
    #         return invalid_response("wrong database name", error, 403)
    #
    #     uid = request.session.uid
    #     # odoo login failed:
    #     if not uid:
    #         info = "authentication failed"
    #         error = "authentication failed"
    #         _logger.error(info)
    #         return invalid_response(401, error, info)
    #
    #     # Generate tokens
    #
    #
    #     access_token = _token.find_one_or_create_token(user_id=uid, create=True)
    #     # Successful response:
    #     return werkzeug.wrappers.Response(
    #         status=200,
    #         content_type="application/json; charset=utf-8",
    #         headers=[("Cache-Control", "no-store"), ("Pragma", "no-cache")],
    #         response=json.dumps(
    #             {
    #                 "token": access_token,
    #                 "username": username,
    #                 "id": uid,
    #                 "name": request.env.user.partner_id.name,
    #                 "admin": request.env.user.is_admin,
    #
    #             }
    #         ),
    #     )

    @http.route("/salesperson/login", methods=["GET"], type='http', auth="none", csrf=False)
    def api_login(self, **post):

        db = post.get("db")
        username = post.get("login")
        password = post.get("password")

        _credentials_includes_in_body = all([db, username, password])
        if not _credentials_includes_in_body:

            _credentials_includes_in_headers = all([db, username, password])
            if not _credentials_includes_in_headers:
                # Empty 'db' or 'username' or 'password:
                return invalid_response(
                    "missing error", "either of the following are missing [db, username,password]", 403,
                )
        # Login in odoo database:
        try:
            request.session.authenticate(db, username, password)
        except AccessError as aee:
            return invalid_response("Access error", "Error: %s" % aee.name)
        except AccessDenied as ade:
            return invalid_response("Access denied", "Login, password or db invalid")
        except Exception as e:
            # Invalid database:
            info = "The database name is not valid {}".format((e))
            error = "invalid_database"
            _logger.error(info)
            return invalid_response("wrong database name", error, 403)

        uid = request.session.uid
        # odoo login failed:
        if not uid:
            info = "authentication failed"
            error = "authentication failed"
            _logger.error(info)
            return invalid_response(401, error, info)

        # Generate tokens
        access_token = request.env["api.access_token"].find_one_or_create_token(user_id=uid, create=True)
        # Successful response:

        user_id=request.env['res.users'].browse(uid)



        return werkzeug.wrappers.Response(
            status=200,
            content_type="application/json; charset=utf-8",
            headers=[("Cache-Control", "no-store"), ("Pragma", "no-cache")],
            response=json.dumps(
                {
                    "message": "Valid",
                    "access_token": access_token,
                    'image': str(user_id.image_1920),
                    'is_admin': user_id.is_admin,
                    'allow_edit_customer_location': user_id.allow_edit_customer_location,
                    'allow_order_outof_location': user_id.allow_order_outof_location,
                    'show_qty': user_id.show_qty,
                    'can_confirm_invoice': user_id.can_confirm_invoice,
                    'can_create_invoice': user_id.can_create_invoice,
                    'can_confirm_order': user_id.can_confirm_order,
                    'company_id': user_id.company_id.id,


                }
            ),
        )

    @http.route("/salesperson/checktoken", methods=["GET"], type="http", auth="none", csrf=False)
    def token(self, **post):
        token=post.get("token")
        user = self.verify_token(token)
        print(token)
        print(user)

        # odoo login failed:
        if not user:
            error = "Not Valid"
            return invalid_response(401, error)

        # Successful response:
        return werkzeug.wrappers.Response(
            status=200,
            content_type="application/json; charset=utf-8",
            headers=[("Cache-Control", "no-store"), ("Pragma", "no-cache")],
            response=json.dumps(
                {
                    "message": "Valid",
                    "token": token,
                    "username": user.login,
                    "id": user.id,
                    "name": user.partner_id.name,

                    'is_admin': user.is_admin,
                    'allow_edit_customer_location': user.allow_edit_customer_location,
                    'allow_order_outof_location': user.allow_order_outof_location,
                    'show_qty': user.show_qty,

                    'can_confirm_invoice': user.can_confirm_invoice,
                    'can_create_invoice': user.can_create_invoice,
                    'can_confirm_order': user.can_confirm_order,
                    'company_id': user.company_id.id,

                }
            ),
        )


    @http.route("/salesperson/set_new_password", methods=["post"], type="http", auth="none", csrf=False)
    def set_new_password(self, **post):
        token=post.get("token")
        new_password=post.get("new_password")
        user = self.verify_token(token)
        print(token)
        print(user)
        print(new_password)

        # odoo login failed:
        if not user:
            error = "Not Valid"
            return invalid_response(401, error)



        if new_password :
            user.password=new_password
        else:
            error = "Missed New Password"
            return invalid_response(401, error)


        # Successful response:
        return werkzeug.wrappers.Response(
            status=200,
            content_type="application/json; charset=utf-8",
            headers=[("Cache-Control", "no-store"), ("Pragma", "no-cache")],
            response=json.dumps(
                {
                    "message": "Suceess",
                    "token": token,
                    "new_password": new_password,


                }
            ),
        )


    @http.route(["/api/auth/token"], methods=["DELETE"], type="http", auth="none", csrf=False)
    def delete(self, **post):
        """Delete a given token"""
        token = request.env["api.access_token"]
        access_token = post.get("access_token")

        access_token = token.search([("token", "=", access_token)], limit=1)
        if not access_token:
            error = "Access token is missing in the request header or invalid token was provided"
            return invalid_response(400, error)
        for token in access_token:
            token.unlink()
        # Successful response:
        return valid_response([{"message": "access token %s successfully deleted" % (access_token,), "delete": True}])
