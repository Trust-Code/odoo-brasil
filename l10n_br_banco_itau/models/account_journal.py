from odoo import fields, models


class AccountJournal(models.Model):
    _inherit = "account.journal"

    l10n_br_use_boleto_itau = fields.Boolean("Emitir Boleto Itaú")
    l10n_br_itau_client_id = fields.Char("Itau Cliend ID")
    l10n_br_itau_client_secret = fields.Char("Itau Client Secret")

    l10n_br_itau_token_expiry = fields.Datetime(
        string="Expiração do Token Itau"
    )
    l10n_br_itau_access_token = fields.Char(string="Access Token Itau")

    l10n_br_itau_carteira = fields.Integer(string="Carteira")
    l10n_br_valor_itau_multa = fields.Float(string="Valor da Multa (%): ")
    l10n_br_valor_itau_juros_mora = fields.Float(
        string="Valor Juros Mora (%): "
    )
