# -*- coding: utf-8 -*-
from odoo import http

# class BrImportInvoiceEletronic(http.Controller):
#     @http.route('/br_import_invoice_eletronic/br_import_invoice_eletronic/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/br_import_invoice_eletronic/br_import_invoice_eletronic/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('br_import_invoice_eletronic.listing', {
#             'root': '/br_import_invoice_eletronic/br_import_invoice_eletronic',
#             'objects': http.request.env['br_import_invoice_eletronic.br_import_invoice_eletronic'].search([]),
#         })

#     @http.route('/br_import_invoice_eletronic/br_import_invoice_eletronic/objects/<model("br_import_invoice_eletronic.br_import_invoice_eletronic"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('br_import_invoice_eletronic.object', {
#             'object': obj
#         })