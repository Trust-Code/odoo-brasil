# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
import tempfile

from decimal import Decimal
from datetime import datetime
from odoo import fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

try:
    from cnab240.tipos import Arquivo
except ImportError:
    _logger.debug('Cannot import cnab240 dependencies.')


class AccountBankStatementImport(models.TransientModel):
    _inherit = 'account.bank.statement.import'

    file_format = fields.Selection(
        selection_add=[('cnab240', 'Cobrança CNAB 240')])

    def _parse_file(self, data_file):
        if self.force_format:
            if self.file_format == 'cnab240':
                self._check_cnab(data_file, raise_error=True)
                return self._parse_cnab(data_file)
            return super(AccountBankStatementImport, self)._parse_file(
                data_file)
        else:
            if self._check_cnab(data_file):
                return self._parse_cnab(data_file)
            return super(AccountBankStatementImport, self)._parse_file(
                data_file)

    def _check_cnab(self, data_file, raise_error=False):
        try:
            cnab240_file = tempfile.NamedTemporaryFile()
            cnab240_file.write(data_file)
            cnab240_file.flush()
            bank = self.get_bank()
            Arquivo(bank, arquivo=open(cnab240_file.name, 'r'))
            return True
        except Exception as e:
            if raise_error:
                raise UserError(u"Arquivo formato inválido:\n%s" % str(e))
            return False

    def get_bank(self):
        bank = self.env['account.journal'].browse(
            self.env.context["journal_id"]).bank_id.bic
        if bank == '237':
            from cnab240.bancos import bradesco
            return bradesco
        elif bank == '756':
            from cnab240.bancos import sicoob
            return sicoob
        elif bank == '001':
            from cnab240.bancos import banco_brasil
            return banco_brasil
        elif bank == '0851':
            from cnab240.bancos import cecred
            return cecred
        elif bank == '341':
            from cnab240.bancos import itau
            return itau
        elif bank == '033':
            from cnab240.bancos import santander
            return santander

    def _parse_cnab(self, data_file, raise_error=False):
        cnab240_file = tempfile.NamedTemporaryFile()
        cnab240_file.write(data_file)
        cnab240_file.flush()

        bank = self.get_bank()
        arquivo = Arquivo(bank, arquivo=open(cnab240_file.name, 'r'))
        transacoes = []
        valor_total = Decimal('0.0')

        for lote in arquivo.lotes:
            for evento in lote.eventos:
                valor = evento.valor_lancamento
                # Apenas liquidação  (Sicoob:6)
                # Liquidação Bradesco (6, 177)
                # Liquidação Santander ('06', '17')
                if evento.servico_codigo_movimento in (6, 17, '06', '17',):
                    valor_total += valor
                    transacoes.append({
                        'name': "%s : %s" % (evento.sacado_nome,
                                             evento.numero_documento),
                        'date': datetime.strptime(
                            str(evento.data_ocorrencia), '%d%m%Y'),
                        'amount': valor,
                        'partner_name': evento.sacado_nome,
                        'ref': evento.numero_documento,
                        'unique_import_id': str(evento.nosso_numero),
                        'nosso_numero': str(evento.nosso_numero),
                    })

        inicio = final = datetime.now()
        if len(transacoes):
            primeira_transacao = min(transacoes, key=lambda x: x["date"])
            ultima_transacao = max(transacoes, key=lambda x: x["date"])
            inicio = primeira_transacao["date"]
            final = ultima_transacao["date"]

        last_bank_stmt = self.env['account.bank.statement'].search(
            [('journal_id', 'in', self.journal_id.ids)],
            order="date desc, id desc", limit=1)
        last_balance = last_bank_stmt and last_bank_stmt[0].balance_end or 0.0

        vals_bank_statement = {
            'name': u"%s - %s até %s" % (
                arquivo.header.nome_do_banco,
                inicio.strftime('%d/%m/%Y'),
                final.strftime('%d/%m/%Y')),
            'date': inicio,
            'balance_start': last_balance,
            'balance_end_real': Decimal(last_balance) + valor_total,
            'transactions': transacoes
        }
        account_number = ''  # str(arquivo.header.cedente_conta)
        if self.force_journal_account:
            account_number = self.journal_id.bank_acc_number
        return (
            'BRL',
            account_number,
            [vals_bank_statement]
        )
