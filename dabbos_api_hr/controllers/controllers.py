# -*- coding: utf-8 -*-
# from odoo import http


# class DabbosApiHr(http.Controller):
#     @http.route('/dabbos_api_hr/dabbos_api_hr', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/dabbos_api_hr/dabbos_api_hr/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('dabbos_api_hr.listing', {
#             'root': '/dabbos_api_hr/dabbos_api_hr',
#             'objects': http.request.env['dabbos_api_hr.dabbos_api_hr'].search([]),
#         })

#     @http.route('/dabbos_api_hr/dabbos_api_hr/objects/<model("dabbos_api_hr.dabbos_api_hr"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('dabbos_api_hr.object', {
#             'object': obj
#         })

