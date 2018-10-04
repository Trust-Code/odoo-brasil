# © 2018 Danimar Ribeiro <danimaribeiro@gmail.com>, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import fields, models


class AccountAccount(models.Model):
    _inherit = 'account.account'

    l10n_br_credit_account_id = fields.Many2one(
        'account.account', string="Credit Account")
