# © 2018 Danimar Ribeiro, Trustcode
# Part of Trustcode. See LICENSE file for full copyright and licensing details.


from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    iugu_api_token = fields.Char(string="IUGU Api Token", size=100)

    l10n_br_payment_interest_account_id = fields.Many2one(
        'account.account', string="Conta para pagamento de juros")
    l10n_br_payment_discount_account_id = fields.Many2one(
        'account.account', string="Conta para desconto de pagamentos")

    l10n_br_interest_account_id = fields.Many2one(
        'account.account', string="Conta para recebimento de juros/multa")
    l10n_br_bankfee_account_id = fields.Many2one(
        'account.account', string="Conta para tarifas bancárias")
    l10n_br_bank_slip_email_template = fields.Many2one(
        'mail.template', string="Template de Email para boleto")
