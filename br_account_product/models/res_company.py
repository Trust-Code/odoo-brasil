# -*- coding: utf-8 -*-
# © 2013 Renato Lima - Akretion
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models
from odoo.addons.br_account.models.br_account import (
    BrTaxDefinition
)


class ResCompany(models.Model):
    _inherit = 'res.company'

    @api.one
    @api.depends('product_tax_definition_line.tax_id')
    def _compute_taxes(self):
        product_taxes = self.env['account.tax']
        for tax in self.product_tax_definition_line:
            product_taxes += tax.tax_id
        self.product_tax_ids = product_taxes

    document_serie_product_ids = fields.Many2many(
        'br_account.document.serie',
        'res_company_l10n_br_account_document_serie', 'company_id',
        'document_serie_product_id', 'Série de Documentos Fiscais',
        domain="[('company_id', '=', active_id),('active','=',True),"
        "('fiscal_type','=','product')]")
    product_tax_definition_line = fields.One2many(
        'br_tax.definition.company.product',
        'company_id', 'Taxes Definitions')
    product_tax_ids = fields.Many2many(
        'account.tax', string='Product Taxes', compute='_compute_taxes',
        store=True)
    fiscal_document_for_product_id = fields.Many2one(
        'br_account.fiscal.document', "Documento Fiscal para produto")


class BrTaxDefinitionCompanyProduct(BrTaxDefinition, models.Model):
    _name = 'br_tax.definition.company.product'

    company_id = fields.Many2one('res.company', 'Empresa')

    _sql_constraints = [
        ('br_tax_definition_tax_id_uniq',
         'unique (tax_id, company_id)',
         u'Imposto já existente nesta empresa!')
    ]
