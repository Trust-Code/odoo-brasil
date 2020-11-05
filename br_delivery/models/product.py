
from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    altura = fields.Integer(string='Altura')
    largura = fields.Integer(string='Largura')
    comprimento = fields.Integer(string='Comprimento')
