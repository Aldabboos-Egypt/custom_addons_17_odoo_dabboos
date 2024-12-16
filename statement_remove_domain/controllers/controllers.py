# -*- coding: utf-8 -*-
# from odoo import http


# class StatementRemoveDomain(http.Controller):
#     @http.route('/statement_remove_domain/statement_remove_domain', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/statement_remove_domain/statement_remove_domain/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('statement_remove_domain.listing', {
#             'root': '/statement_remove_domain/statement_remove_domain',
#             'objects': http.request.env['statement_remove_domain.statement_remove_domain'].search([]),
#         })

#     @http.route('/statement_remove_domain/statement_remove_domain/objects/<model("statement_remove_domain.statement_remove_domain"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('statement_remove_domain.object', {
#             'object': obj
#         })

