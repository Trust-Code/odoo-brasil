# -*- coding: utf-8 -*-

from odoo import models, fields, api

# class br_import_invoice_eletronic(models.Model):
#     _name = 'br_import_invoice_eletronic.br_import_invoice_eletronic'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         self.value2 = float(self.value) / 100