# © 2020 Danimar Ribeiro, Trustcode
# Part of Trustcode. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    altura = fields.Float(string=u'Altura')
    largura = fields.Float(string=u'Largura')
    diametro = fields.Float(string=u'Diâmetro')
    comprimento = fields.Float(string=u'Comprimento')
