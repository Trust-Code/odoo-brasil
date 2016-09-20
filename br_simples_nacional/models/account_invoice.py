# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro <danimaribeiro@gmail.com>, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import api, fields, models
from odoo.addons.br_account.models.res_company import COMPANY_FISCAL_TYPE


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    @api.model
    def _default_company_fiscal_type(self):
        if self.invoice_id:
            return self.invoice_id.company_id.fiscal_type
        company = self.env['res.company'].browse(self.env.user.company_id.id)
        return company.fiscal_type

    @api.model
    def default_get(self, fields):
        res = super(AccountInvoiceLine, self).default_get(fields)
        if "pis_cst" not in res:
            res['pis_cst'] = '99'
        if "cofins_cst" not in res:
            res['cofins_cst'] = '99'
        if "ipi_cst" not in res:
            res['ipi_cst'] = '99'
        return res

    company_fiscal_type = fields.Selection(
        COMPANY_FISCAL_TYPE,
        default=_default_company_fiscal_type,
        string="Regime Tributário")

    tax_icms_id = fields.Many2one('account.tax', string="ICMS",
                                  domain=[('domain', '=', 'simples')])

    @api.onchange('tax_icms_id')
    def _simples_nacional_onchange_tax_icms_id(self):
        if self.tax_icms_id:
            self.icms_percent_credit = self.tax_icms_id.percent_credit
