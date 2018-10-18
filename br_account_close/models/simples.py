# © 2018 Danimar Ribeiro <danimaribeiro@gmail.com>, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class l10nBrTaxationSimples(models.Model):
    _name = 'l10n_br.taxation.simples'
    _order = 'start_revenue'

    tax_id = fields.Many2one('account.tax', string="Tax")
    start_revenue = fields.Float(string="Start Revenue")
    end_revenue = fields.Float(string="End Revenue")
    amount_tax = fields.Float(string="Tax")
    amount_deduction = fields.Float(string="Amount to deduct")
    company_id = fields.Many2one(
        'res.company', related="tax_id.company_id", readonly=True)
