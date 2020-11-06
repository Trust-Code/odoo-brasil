# © 2019 Danimar Ribeiro, Trustcode
# Part of Trustcode. See LICENSE file for full copyright and licensing details.

import requests
from datetime import datetime
from odoo import fields, models, api
from odoo.exceptions import UserError


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    def __get_bank_statements_available_sources(self):
        vals = super(AccountJournal, self).__get_bank_statements_available_sources()
        vals.append(("sicoob_sync", "Sincronização Sicoob"))
        return vals

    def _default_sicoob_url(self):
        return self.env['ir.config_parameter'].sudo().get_param('web.base.url')

    l10n_br_bank_branch_number = fields.Char(string="Número da Agência")
    l10n_br_sicoob_client_id = fields.Char(string="Client Id", size=100)
    l10n_br_sicoob_client_secret = fields.Char(string="Client Secret", size=100)
    l10n_br_sicoob_token_basic = fields.Char(string="Token Basic", size=100)
    l10n_br_sicoob_url_base = fields.Char(string="URL de Retorno Sicoob", size=100,
                                          default=_default_sicoob_url)

    temp_access_token = fields.Char(string="Access Token Sicoob", size=150)

    @api.onchange('bank_account_id')
    def _onchange_bank_account(self):
        self.ensure_one()
        self.l10n_br_bank_branch_number = self.bank_account_id.l10n_br_branch_number

    def action_authorize_odoo(self):
        if not self.bank_account_id:
            raise UserError('Configure uma conta bancária para autorizar!')
        if not self.bank_account_id.l10n_br_branch_number:
            raise UserError('Configure a agência da conta bancária!')
        if not self.bank_account_id.acc_number:
            raise UserError('Configure o número da conta bancária!')
        if not self.l10n_br_sicoob_client_id:
            raise UserError('Configure o Client ID!')
        if not self.l10n_br_sicoob_client_secret:
            raise UserError('Configure o Client Secret!')
        if not self.l10n_br_sicoob_token_basic:
            raise UserError('Configure o Token Basic!')
        if not self.l10n_br_sicoob_url_base:
            raise UserError('Configure a URL base de retorno!')

        return_url = '%s/sicoob/authorization?journal=%s' % (
            self.l10n_br_sicoob_url_base, self.id)
        url = 'https://sandbox.sicoob.com.br/oauth2/authorize?response_type=code&redirect_uri=%s&client_id=%s' \
              '&cooperativa=%s&contaCorrente=%s&scope=cco_extrato+cco_saldo' % (
                  return_url, self.l10n_br_sicoob_client_id,
                  self.bank_account_id.l10n_br_branch_number or '',
                  self.bank_account_id.acc_number or '',
              )
        return {
            'type': 'ir.actions.act_url',
            'url': url,
            'target': 'self',
        }

    def action_synchronize_statement(self):
        url = 'https://sandbox.sicoob.com.br/conta-corrente/extrato/10/2020'
        headers = {
            "Authorization": "Bearer %s" % self.temp_access_token
        }
        r = requests.get(url, headers=headers)
        if r.status_code == 200:
            extrato = r.json()
            saldo = extrato['resultado']['saldo']
            transacoes = extrato['resultado']['transacoes']

            line_ids = []
            for transacao in transacoes:
                data = datetime.strptime(
                    transacao['data'], '%Y-%m-%dT%H:%M:%S.%fZ')
                valor = transacao['valor']
                if transacao['tipo'] == 'DEBITO':
                    valor *= -1
                line_ids.append((0, 0, {
                    'date': data,
                    'name': transacao['descricao'],
                    'ref': transacao['numeroDocumento'],
                    'amount': valor,
                }))

            statement = self.env['account.bank.statement'].create({
                'name': 'Sincronização online',
                'journal_id': self.id,
                'date': datetime.today(),
                'company_id': self.company_id.id,
                'balance_start': 0.0,
                'balance_end_real': saldo,
                'line_ids': line_ids,
            })
            action = self.env.ref(
                'account.action_bank_reconcile_bank_statements')
            return {
                'name': action.name,
                'tag': action.tag,
                'context': {
                    'statement_ids': [statement.id],
                    'notifications': []
                },
                'type': 'ir.actions.client',
            }
        elif r.status_code == 401:
            raise UserError(
                'O token de acesso está expirado!\n\
Faça a autorização novamente no cadastro de diários')
        else:
            raise UserError(r.reason)
