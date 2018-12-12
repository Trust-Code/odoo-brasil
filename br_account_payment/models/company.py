from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    l10n_br_pymt_fine_account_id = fields.Many2one(
        'account.account',
        string="Conta para pagamento de multa",
        domain=[('user_type_id.type', '=', 'payable')])

    l10n_br_pymt_interest_account_id = fields.Many2one(
        'account.account',
        string="Conta para pagamento de juros",
        domain=[('user_type_id.type', '=', 'payable')])

    l10n_br_interest_account_id = fields.Many2one(
        'account.account',
        string="Conta para recebimento de juros",
        domain=[('user_type_id', '=', 'receivable')])

    l10n_br_fine_account_id = fields.Many2one(
        'account.account',
        string="Conta para recebimento de multa",
        domain=[('user_type_id.type', '=', 'receivable')])
