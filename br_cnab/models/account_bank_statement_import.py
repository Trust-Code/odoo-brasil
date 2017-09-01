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

            journal_id = self.env.context['journal_id']
            if self.force_journal_account:
                journal_id = self.journal_id.id

            bank = self.get_bank(journal_id)
            Arquivo(bank, arquivo=open(cnab240_file.name, 'r'))
            return True
        except Exception as e:
            if raise_error:
                raise UserError(u"Arquivo formato inválido:\n%s" % str(e))
            return False

    def _get_nosso_numero(self, journal_id, nosso_numero):
        # TODO Quando outros bancos modificar aqui
        bank = self.env['account.journal'].browse(journal_id).bank_id.bic
        if bank == '237':  # Bradesco
            return int(nosso_numero[8:19])
        elif bank == '756':
            return int(nosso_numero[:9])
        elif bank == '033':
            return int(nosso_numero[:-1])
        elif bank == '748':
            return int(nosso_numero[:-1])
        elif bank == '001':
            return int(nosso_numero[10:])
        return nosso_numero

    def get_bank(self, journal_id):
        bank = self.env['account.journal'].browse(journal_id).bank_id.bic
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
        elif bank == '748':
            from cnab240.bancos import sicredi
            return sicredi
        else:
            raise UserError(u'Banco ainda não implementado: %s' % bank)

    def _parse_cnab(self, data_file, raise_error=False):
        cnab240_file = tempfile.NamedTemporaryFile()
        cnab240_file.write(data_file)
        cnab240_file.flush()

        journal_id = self.env.context['journal_id']
        if self.force_journal_account:
            journal_id = self.journal_id.id

        bank = self.get_bank(journal_id)
        arquivo = Arquivo(bank, arquivo=open(cnab240_file.name, 'r'))
        transacoes = []
        valor_total = Decimal('0.0')
        for lote in arquivo.lotes:
            for evento in lote.eventos:
                valor = evento.valor_lancamento
                # Apenas liquidação  (Sicoob:6)
                # Liquidação Banco do Brasil (6, 17)
                # Liquidação Bradesco (6, 177)
                # Liquidação Santander ('06', '17')
                if evento.servico_codigo_movimento in (6, 17, '06', '17',):
                    valor_total += valor

                    nosso_numero = self._get_nosso_numero(
                        journal_id, evento.nosso_numero)

                    move_line = self.env['account.move.line'].search(
                        [('nosso_numero', '=', nosso_numero)])

                    transacoes.append({
                        'name': "%s : %s" % (
                            move_line.partner_id.name or evento.sacado_nome,
                            evento.numero_documento or "%s: %s" % (
                                move_line.move_id.name, move_line.name)),
                        'date': datetime.strptime(
                            str(evento.data_ocorrencia), '%d%m%Y'),
                        'amount': valor,
                        'partner_name':
                        move_line.partner_id.name or evento.sacado_nome,
                        'partner_id': move_line.partner_id.id,
                        'ref': evento.numero_documento,
                        'unique_import_id': str(evento.nosso_numero),
                        'nosso_numero': nosso_numero,
                    })

        inicio = final = datetime.now()
        if len(transacoes):
            primeira_transacao = min(transacoes, key=lambda x: x["date"])
            ultima_transacao = max(transacoes, key=lambda x: x["date"])
            inicio = primeira_transacao["date"]
            final = ultima_transacao["date"]

        last_bank_stmt = self.env['account.bank.statement'].search(
            [('journal_id', '=', journal_id)],
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
