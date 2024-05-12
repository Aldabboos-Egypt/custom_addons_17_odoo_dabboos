# -*- coding: utf-8 -*-
# from odoo import http


# class DailySalepersonPerformance(http.Controller):
#     @http.route('/daily_saleperson_performance/daily_saleperson_performance/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/daily_saleperson_performance/daily_saleperson_performance/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('daily_saleperson_performance.listing', {
#             'root': '/daily_saleperson_performance/daily_saleperson_performance',
#             'objects': http.request.env['daily_saleperson_performance.daily_saleperson_performance'].search([]),
#         })

#     @http.route('/daily_saleperson_performance/daily_saleperson_performance/objects/<model("daily_saleperson_performance.daily_saleperson_performance"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('daily_saleperson_performance.object', {
#             'object': obj
#         })
