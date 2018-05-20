# -*- coding: utf-8 -*-
from odoo import http

# class BrDfe(http.Controller):
#     @http.route('/br_dfe/br_dfe/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/br_dfe/br_dfe/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('br_dfe.listing', {
#             'root': '/br_dfe/br_dfe',
#             'objects': http.request.env['br_dfe.br_dfe'].search([]),
#         })

#     @http.route('/br_dfe/br_dfe/objects/<model("br_dfe.br_dfe"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('br_dfe.object', {
#             'object': obj
#         })