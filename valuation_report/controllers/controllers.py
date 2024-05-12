# -*- coding: utf-8 -*-
# from odoo import http


# class ValuationReports(http.Controller):
#     @http.route('/valuation_reports/valuation_reports/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/valuation_reports/valuation_reports/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('valuation_reports.listing', {
#             'root': '/valuation_reports/valuation_reports',
#             'objects': http.request.env['valuation_reports.valuation_reports'].search([]),
#         })

#     @http.route('/valuation_reports/valuation_reports/objects/<model("valuation_reports.valuation_reports"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('valuation_reports.object', {
#             'object': obj
#         })
