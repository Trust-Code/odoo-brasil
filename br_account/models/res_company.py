# © 2009 Renato Lima - Akretion
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields
from odoo.addons import decimal_precision as dp

COMPANY_FISCAL_TYPE = [
    ('1', 'Simples Nacional'),
    ('2', 'Simples Nacional – excesso de sublimite de receita bruta'),
    ('3', 'Regime Normal')
]

COMPANY_FISCAL_TYPE_DEFAULT = '3'


class ResCompany(models.Model):
    _name = 'res.company'
    _inherit = ['res.company', 'br.localization.filtering']

    l10n_br_fiscal_document_for_product_id = fields.Many2one(
        'br_account.fiscal.document', "Documento Fiscal para produto",
        oldname='fiscal_document_for_product_id')

    l10n_br_annual_revenue = fields.Float(
        'Faturamento Anual', required=True,
        digits=dp.get_precision('Account'), default=0.00,
        help=u"Faturamento Bruto dos últimos 12 meses",
        oldname='annual_revenue')
    l10n_br_fiscal_type = fields.Selection(
        COMPANY_FISCAL_TYPE, u'Regime Tributário', required=True,
        default=COMPANY_FISCAL_TYPE_DEFAULT, oldname='fiscaltype')
    l10n_br_cnae_main_id = fields.Many2one(
        'br_account.cnae', u'CNAE Primário', oldname='cnae_main_id')
    l10n_br_cnae_secondary_ids = fields.Many2many(
        'br_account.cnae', 'res_company_br_account_cnae',
        'company_id', 'cnae_id', u'CNAE Secundários',
        oldname='cnae_secondary_ids')

    l10n_br_accountant_id = fields.Many2one(
        'res.partner', string="Contador", oldname='accountant_id')
