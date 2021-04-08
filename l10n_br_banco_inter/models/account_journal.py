# © 2021 Danimar Ribeiro, Trustcode
# Part of Trustcode. See LICENSE file for full copyright and licensing details.

import requests
from datetime import datetime, timedelta
from odoo import fields, models


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    l10n_br_use_boleto_inter = fields.Boolean('Emitir Boleto Inter')
    l10n_br_inter_cert = fields.Binary('Certificado API Inter')
    l10n_br_inter_key = fields.Binary('Chave API Inter')

    l10n_br_valor_multa = fields.Float(string="Valor da Multa (%): ")
    l10n_br_valor_juros_mora = fields.Float(string="Valor Juros Mora (%): ")
    l10n_br_boleto_instrucoes = fields.Char(string="Instruções do Boleto", size=400)