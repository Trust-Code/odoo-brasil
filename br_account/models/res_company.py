# -*- coding: utf-8 -*-
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
    _inherit = 'res.company'

    fiscal_document_for_product_id = fields.Many2one(
        'br_account.fiscal.document', "Product Fiscal Document")

    annual_revenue = fields.Float(
        'Annual Revenue', required=True,
        digits=dp.get_precision('Account'), default=0.00,
        help=u"Gross Revenue for the past 12 months")
    fiscal_type = fields.Selection(
        COMPANY_FISCAL_TYPE, u'Tax Regime', required=True,
        default=COMPANY_FISCAL_TYPE_DEFAULT)
    cnae_main_id = fields.Many2one(
        'br_account.cnae', u'Primary CNAE')
    cnae_secondary_ids = fields.Many2many(
        'br_account.cnae', 'res_company_br_account_cnae',
        'company_id', 'cnae_id', u'Secondaries CNAE')

    accountant_id = fields.Many2one('res.partner', string="Accountant")
