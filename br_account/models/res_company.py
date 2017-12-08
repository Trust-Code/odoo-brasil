# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields
from odoo.addons import decimal_precision as dp
import datetime

COMPANY_FISCAL_TYPE = [
    ('1', 'Simples Nacional'),
    ('2', 'Simples Nacional – excesso de sublimite de receita bruta'),
    ('3', 'Regime Normal')
]

COMPANY_FISCAL_TYPE_DEFAULT = '3'


class ResCompany(models.Model):
    _inherit = 'res.company'

    fiscal_document_for_product_id = fields.Many2one(
        'br_account.fiscal.document', "Documento Fiscal para produto")

    annual_revenue = fields.Float(
        'Faturamento Anual', required=True,
        digits=dp.get_precision('Account'), default=0.00,
        help=u"Faturamento Bruto dos últimos 12 meses")
    fiscal_type = fields.Selection(
        COMPANY_FISCAL_TYPE, u'Regime Tributário', required=True,
        default=COMPANY_FISCAL_TYPE_DEFAULT)
    cnae_main_id = fields.Many2one(
        'br_account.cnae', u'CNAE Primário')
    cnae_secondary_ids = fields.Many2many(
        'br_account.cnae', 'res_company_br_account_cnae',
        'company_id', 'cnae_id', u'CNAE Secundários')

    accountant_id = fields.Many2one('res.partner', string="Contador")

    taxes_ids = fields.One2many('br_account.taxes.close',
                                'company_id',
                                string='Impostos')

    def get_gross_revenue_last_year(self):
        gross_revenues = {}
        date_max = datetime.date.today()
        date_min = date_max - datetime.timedelta(days=365)
        for simples_nacional_id in self.taxes_ids:
            account_lines = self.env['account.move.line'].search([
                ('account_id', '=', simples_nacional_id.account_id),
                ('create_date', '>=', date_min),
                ('create_date', '<=', date_max)])
            gross_revenue = 0
            for line in account_lines:
                gross_revenue += line.credit
            gross_revenues.update({simples_nacional_id: gross_revenue})
        return gross_revenues

    def compute_new_taxes_simples_nacional(self):
        gross_revenues = self.get_gross_revenue_last_year()
        taxes = {}
        for simples_nacional_id in gross_revenues.keys():
            default_tax = simples_nacional_id.tax
            pd = simples_nacional_id.deducao
            gross_revenue = gross_revenues[simples_nacional_id]
            tax = (default_tax*gross_revenue - pd)/gross_revenue
            taxes.update({simples_nacional_id: tax})
        return taxes

    def compute_icms_credit_simples_nacional(self):
        icms = {}
        taxes = self.compute_new_taxes_simples_nacional()
        for simples_nacional_id in taxes.keys():
            icms_credit = simples_nacional_id.icms_percent*taxes[
                simples_nacional_id]
            icms.update({simples_nacional_id: icms_credit})
        return icms
