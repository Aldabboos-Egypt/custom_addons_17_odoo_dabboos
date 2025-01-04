# -*- coding: utf-8 -*-
# from odoo import http


# class EmployeeLocations(http.Controller):
#     @http.route('/employee_locations/employee_locations', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/employee_locations/employee_locations/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('employee_locations.listing', {
#             'root': '/employee_locations/employee_locations',
#             'objects': http.request.env['employee_locations.employee_locations'].search([]),
#         })

#     @http.route('/employee_locations/employee_locations/objects/<model("employee_locations.employee_locations"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('employee_locations.object', {
#             'object': obj
#         })

