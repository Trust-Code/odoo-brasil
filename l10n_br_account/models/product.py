from odoo import api, fields, models
from .cst import ORIGEM_PROD


class ProductFiscalCategory(models.Model):
    _name = 'product.fiscal.category'
    _description = 'Categoria Fiscal'

    name = fields.Char('Descrição', required=True)


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    l10n_br_origin = fields.Selection(ORIGEM_PROD, 'Origem', default='0')
    l10n_br_ncm_id = fields.Many2one(
        'account.ncm', string="Classificação Fiscal (NCM)")
    service_type_id = fields.Many2one('account.service.type', 'Tipo de Serviço')
    service_code = fields.Char(string='Código no Município')
    service_code_description = fields.Char(string='Descrição Código do Município')


    l10n_br_cest = fields.Char(string="CEST", size=10, help="Código Especificador da Substituição Tributária")
    l10n_br_fiscal_category_id = fields.Many2one('product.fiscal.category', string='Categoria Fiscal')
    l10n_br_extipi = fields.Char(string="EX TIPI", size=3)
    l10n_br_fiscal_benefit = fields.Char(string="Benefício Fiscal", size=10)

