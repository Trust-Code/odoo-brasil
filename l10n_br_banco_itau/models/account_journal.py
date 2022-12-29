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

    l10n_br_valor_boleto_multa = fields.Float(string="Valor da Multa (%): ")
    l10n_br_valor_boleto_juros_mora = fields.Float(
        string="Valor Juros Mora (%): "
    )
    l10n_br_boleto_carteira = fields.Char(string="Carteira")
    l10n_br_boleto_instr = fields.Char(string="Instruções")
    l10n_br_cnab_code = fields.Char("Código Convênio", size=20)
    l10n_br_boleto_aceite = fields.Selection(
        [("S", "Sim"), ("N", "Não")], string="Aceite", default="N"
    )
    l10n_br_boleto_especie = fields.Selection(
        [
            ("01", "DUPLICATA MERCANTIL"),
            ("02", "NOTA PROMISSÓRIA"),
            ("03", "NOTA DE SEGURO"),
            ("04", "MENSALIDADE ESCOLAR"),
            ("05", "RECIBO"),
            ("06", "CONTRATO"),
            ("07", "COSSEGUROS"),
            ("08", "DUPLICATA DE SERVIÇO"),
            ("09", "LETRA DE CÂMBIO"),
            ("13", "NOTA DE DÉBITOS"),
            ("15", "DOCUMENTO DE DÍVIDA"),
            ("16", "ENCARGOS CONDOMINIAIS"),
            ("17", "CONTA DE PRESTAÇÃO DE SERVIÇOS"),
            ("99", "DIVERSOS"),
        ],
        string="Espécie do Título",
        default="01",
    )
