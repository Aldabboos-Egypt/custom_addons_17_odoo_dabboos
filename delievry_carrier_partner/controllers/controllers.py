# -*- coding: utf-8 -*-
# from odoo import http


# class DelievryCarrierPartner(http.Controller):
#     @http.route('/delievry_carrier_partner/delievry_carrier_partner', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/delievry_carrier_partner/delievry_carrier_partner/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('delievry_carrier_partner.listing', {
#             'root': '/delievry_carrier_partner/delievry_carrier_partner',
#             'objects': http.request.env['delievry_carrier_partner.delievry_carrier_partner'].search([]),
#         })

#     @http.route('/delievry_carrier_partner/delievry_carrier_partner/objects/<model("delievry_carrier_partner.delievry_carrier_partner"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('delievry_carrier_partner.object', {
#             'object': obj
#         })

