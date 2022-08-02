# © 2021 Danimar Ribeiro, Trustcode
# Part of Trustcode. See LICENSE file for full copyright and licensing details.

from datetime import datetime
from odoo import fields, models
from odoo.exceptions import UserError


class AccountBankStatement(models.Model):
    _inherit = "account.bank.statement"

    end_date = fields.Date(string="Data Final")


class AccountJournal(models.Model):
    _name = 'account.journal'
    _inherit = ['account.journal', 'banco.inter.mixin']

    l10n_br_use_boleto_inter = fields.Boolean('Emitir Boleto Inter')
    l10n_br_inter_cert = fields.Binary('Certificado API Inter')
    l10n_br_inter_key = fields.Binary('Chave API Inter')
    l10n_br_inter_client_id = fields.Char(string="Client ID")
    l10n_br_inter_client_secret = fields.Char(string="Client Secret")

    l10n_br_valor_multa = fields.Float(string="Valor da Multa (%): ")
    l10n_br_valor_juros_mora = fields.Float(string="Valor Juros Mora (%): ")

    def sync_bank_statement_online_inter(self, start=None, end=None):
        overlap = self.env["account.bank.statement"].search_count([('date', '>=', start), ('date', '<=', end)])
        overlap2 = self.env["account.bank.statement"].search_count([('end_date', '>=', start), ('end_date', '<=', end)])
        overlap3 = self.env["account.bank.statement"].search_count([('date', '<=', start), ('end_date', '>=', end)])
        if overlap or overlap2 or overlap3:
            raise UserError("Extrato já existente para o intervalo solicitado!")

        inter_statement = self.get_bank_statement_inter(self, start, end)

        statement = self.env['account.bank.statement'].create({
            'name': "Extrato de {0} até {1}".format(start.strftime("%d-%m-%Y"), end.strftime("%d-%m-%Y")),
            'journal_id': self.id,
            'date': start,
            'end_date': end,
            'balance_start': inter_statement["start_balance"],
            'balance_end_real': inter_statement["end_balance"],
        })

        for titulo in inter_statement["transactions"]:
            self.env['account.bank.statement.line'].create({
                'statement_id': statement.id,
                'date': titulo["dataEntrada"],
                'name': titulo['titulo'],
                'ref': titulo['descricao'],
                'amount': float(titulo['valor']) if titulo["tipoOperacao"] == "C" else (float(titulo['valor']) * -1.0),
            })

        return statement.action_bank_reconcile_bank_statements()