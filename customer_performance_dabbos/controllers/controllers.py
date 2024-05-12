# -*- coding: utf-8 -*-
# from odoo import http


# class CustomerPerformanceDabbos(http.Controller):
#     @http.route('/customer_performance_dabbos/customer_performance_dabbos/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/customer_performance_dabbos/customer_performance_dabbos/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('customer_performance_dabbos.listing', {
#             'root': '/customer_performance_dabbos/customer_performance_dabbos',
#             'objects': http.request.env['customer_performance_dabbos.customer_performance_dabbos'].search([]),
#         })

#     @http.route('/customer_performance_dabbos/customer_performance_dabbos/objects/<model("customer_performance_dabbos.customer_performance_dabbos"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('customer_performance_dabbos.object', {
#             'object': obj
#         })
