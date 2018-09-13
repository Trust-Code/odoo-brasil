# © 2018 Danimar Ribeiro <danimaribeiro@gmail.com>, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class l10nBrTaxationSimples(models.Model):
    _name = 'l10n_br.taxation.simples'

    start_revenue = fields.Float(string="Start Revenue")
    end_revenue = fields.Float(string="End Revenue")
    amount_tax = fields.Float(string="Tax")
    amount_deduction = fields.Float(string="Amount to deduct")
    account_ids = fields.Many2many('account.account', string="Accounts")
    company_id = fields.Many2one('res.company')
