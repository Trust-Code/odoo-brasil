# © 2018 Danimar Ribeiro <danimaribeiro@gmail.com>, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import datetime
from odoo import api, fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

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
