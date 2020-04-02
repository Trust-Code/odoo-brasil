from odoo import api, fields, models
from .cst import ORIGEM_PROD


class ProductFiscalCategory(models.Model):
    _name = 'product.fiscal.category'
    _description = 'Categoria Fiscal'

    name = fields.Char('Descrição', required=True)


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    origin = fields.Selection(ORIGEM_PROD, 'Origem', default='0')
    # fiscal_classification_id = fields.Many2one(
    #     'product.fiscal.classification', string=u"Classificação Fiscal (NCM)")
    service_type_id = fields.Many2one('account.service.type', 'Tipo de Serviço')
    service_code = fields.Char(string='Código no Município')

    cest = fields.Char(string="CEST", size=10, help="Código Especificador da Substituição Tributária")
    fiscal_category_id = fields.Many2one('product.fiscal.category', string='Categoria Fiscal')

