from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    l10n_br_payment_interest_account_id = fields.Many2one(
        'account.account', string="Conta para pagamento de juros")
    l10n_br_payment_discount_account_id = fields.Many2one(
        'account.account', string="Conta para pagamento de multa")

    l10n_br_interest_account_id = fields.Many2one(
        'account.account', string="Conta para recebimento de juros/multa")
    l10n_br_bankfee_account_id = fields.Many2one(
        'account.account', string="Conta para tarifas bancárias")
