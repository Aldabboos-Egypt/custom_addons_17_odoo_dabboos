# -*- coding: utf-8 -*-
# from odoo import http


# class CpnDabbos(http.Controller):
#     @http.route('/cpn_dabbos/cpn_dabbos', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/cpn_dabbos/cpn_dabbos/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('cpn_dabbos.listing', {
#             'root': '/cpn_dabbos/cpn_dabbos',
#             'objects': http.request.env['cpn_dabbos.cpn_dabbos'].search([]),
#         })

#     @http.route('/cpn_dabbos/cpn_dabbos/objects/<model("cpn_dabbos.cpn_dabbos"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('cpn_dabbos.object', {
#             'object': obj
#         })

