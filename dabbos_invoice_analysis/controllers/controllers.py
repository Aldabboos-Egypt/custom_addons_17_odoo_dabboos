# -*- coding: utf-8 -*-
# from odoo import http


# class DabbosInvoiceAnalysis(http.Controller):
#     @http.route('/dabbos_invoice_analysis/dabbos_invoice_analysis', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/dabbos_invoice_analysis/dabbos_invoice_analysis/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('dabbos_invoice_analysis.listing', {
#             'root': '/dabbos_invoice_analysis/dabbos_invoice_analysis',
#             'objects': http.request.env['dabbos_invoice_analysis.dabbos_invoice_analysis'].search([]),
#         })

#     @http.route('/dabbos_invoice_analysis/dabbos_invoice_analysis/objects/<model("dabbos_invoice_analysis.dabbos_invoice_analysis"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('dabbos_invoice_analysis.object', {
#             'object': obj
#         })

