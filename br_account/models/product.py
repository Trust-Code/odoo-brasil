# © 2009  Gabriel C. Stabel
# © 2009  Renato Lima - Akretion
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api
from .cst import ORIGEM_PROD


class ProductTemplate(models.Model):
    _name = 'product.template'
    _inherit = ['product.template', 'br.localization.filtering']

    l10n_br_fiscal_type = fields.Selection(
        [('service', u'Serviço'), ('product', 'Produto')], 'Tipo Fiscal',
        required=True, default='product', oldname='fiscal_type')
    l10n_br_origin = fields.Selection(
        ORIGEM_PROD, 'Origem', default='0', oldname='origin')
    l10n_br_fiscal_classification_id = fields.Many2one(
        'product.fiscal.classification', string=u"Classificação Fiscal (NCM)",
        oldname='fiscal_classification_id')
    l10n_br_service_type_id = fields.Many2one(
        'br_account.service.type', u'Tipo de Serviço',
        oldname='service_type_id')
    l10n_br_cest = fields.Char(
        string="CEST", size=10,
        help=u"Código Especificador da Substituição Tributária",
        oldname='cest')
    l10n_br_fiscal_observation_ids = fields.Many2many(
        'br_account.fiscal.observation', string=u"Mensagens Doc. Eletrônico",
        oldname='fiscal_observation_ids')
    l10n_br_fiscal_category_id = fields.Many2one(
        'br_account.fiscal.category', string='Categoria Fiscal',
        oldname='fiscal_category_id')

    @api.onchange('type')
    def onchange_product_type(self):
        self.l10n_br_fiscal_type = ('service'
                                    if self.type == 'service' else 'product')

    @api.onchange('l10n_br_fiscal_type')
    def onchange_product_fiscal_type(self):
        self.type = ('service'
                     if self.l10n_br_fiscal_type == 'service' else 'consu')
