# -*- coding: utf-8 -*-
from odoo import http

# class BrDfeImportInvoice(http.Controller):
#     @http.route('/br_dfe_import_invoice/br_dfe_import_invoice/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/br_dfe_import_invoice/br_dfe_import_invoice/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('br_dfe_import_invoice.listing', {
#             'root': '/br_dfe_import_invoice/br_dfe_import_invoice',
#             'objects': http.request.env['br_dfe_import_invoice.br_dfe_import_invoice'].search([]),
#         })

#     @http.route('/br_dfe_import_invoice/br_dfe_import_invoice/objects/<model("br_dfe_import_invoice.br_dfe_import_invoice"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('br_dfe_import_invoice.object', {
#             'object': obj
#         })