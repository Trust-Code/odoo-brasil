# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
import tempfile
import StringIO

from datetime import datetime
from odoo import fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

try:
    from cnab240.bancos import sicoob
    from cnab240.tipos import Arquivo
    from ofxparse import OfxParser
except ImportError:
    _logger.debug('Cannot import cnab240 or ofxparse dependencies.')


class AccountBankStatementImport(models.TransientModel):
    _inherit = 'account.bank.statement.import'

    force_format = fields.Boolean(string=u'Forçar formato', default=False)
    file_format = fields.Selection([('cnab240', 'Extrato CNAB 240'),
                                    ('ofx', 'Extrato OFX')],
                                   string="Formato do Arquivo",
                                   default='cnab240')
    force_journal_account = fields.Boolean(string=u"Forçar conta bancária?")
    journal_id = fields.Many2one('account.journal', string=u"Conta Bancária",
                                 domain=[('type', '=', 'bank')])

    def _parse_file(self, data_file):
        if self.force_format:
            if self.file_format == 'cnab240':
                self._check_cnab(data_file, raise_error=True)
                return self._parse_cnab(data_file)
            else:
                self._check_ofx(data_file, raise_error=True)
                return self._parse_ofx(data_file)
        else:
            if self._check_cnab(data_file):
                return self._parse_cnab(data_file)
            if self._check_ofx(data_file):
                return self._parse_ofx(data_file)
            return super(AccountBankStatementImport, self)._parse_file(
                data_file)

    def _check_cnab(self, data_file, raise_error=False):
        try:
            cnab240_file = tempfile.NamedTemporaryFile()
            cnab240_file.write(data_file)
            cnab240_file.flush()
            Arquivo(sicoob, arquivo=open(cnab240_file.name, 'r'))
            return True
        except Exception as e:
            if raise_error:
                raise UserError(u"Arquivo formato inválido:\n%s" % str(e))
            return False

    def _check_ofx(self, data_file, raise_error=False):
        try:
            data_file = data_file.replace('\r\n', '\n').replace('\r', '\n')
            OfxParser.parse(StringIO.StringIO(data_file))
            return True
        except Exception as e:
            if raise_error:
                raise UserError(u"Arquivo formato inválido:\n%s" % str(e))
            return False

    def _parse_ofx(self, data_file):
        data_file = data_file.replace('\r\n', '\n').replace('\r', '\n')
        ofx = OfxParser.parse(StringIO.StringIO(data_file))
        transacoes = []
        total = 0.0
        index = 1  # Some banks don't use a unique transaction id, we make one
        for account in ofx.accounts:
            for transacao in account.statement.transactions:
                transacoes.append({
                    'date': transacao.date,
                    'name': transacao.payee + (
                        transacao.memo and ': ' + transacao.memo or ''),
                    'ref': transacao.id,
                    'amount': transacao.amount,
                    'unique_import_id': "%s-%s" % (transacao.id, index)
                })
                total += float(transacao.amount)
                index += 1
        # Really? Still using Brazilian Cruzeiros :/
        if ofx.account.statement.currency.upper() == "BRC":
            ofx.account.statement.currency = "BRL"

        journal = self.journal_id
        if not self.force_journal_account:
            dummy, journal = self._find_additional_data(
                ofx.account.statement.currency, ofx.account.number)

        name = u"%s - %s até %s" % (
            journal.name,
            ofx.account.statement.start_date.strftime('%d/%m/%Y'),
            ofx.account.statement.end_date.strftime('%d/%m/%Y')
        )
        vals_bank_statement = {
            'name': name,
            'transactions': transacoes,
            'balance_start': ofx.account.statement.balance,
            'balance_end_real': float(ofx.account.statement.balance) + total,
        }

        account_number = ofx.account.number
        if self.force_journal_account:
            account_number = self.journal_id.bank_acc_number
        return (
            ofx.account.statement.currency,
            account_number,
            [vals_bank_statement]
        )

    def _parse_cnab(self, data_file, raise_error=False):
        cnab240_file = tempfile.NamedTemporaryFile()
        cnab240_file.write(data_file)
        cnab240_file.flush()

        arquivo = Arquivo(sicoob, arquivo=open(cnab240_file.name, 'r'))
        transacoes = []
        for lote in arquivo.lotes:
            for evento in lote.eventos:
                valor = evento.valor_lancamento
                if evento.tipo_lancamento == 'D':
                    valor *= -1
                transacoes.append({
                    'name': evento.descricao_historico,
                    'date': datetime.strptime(
                        str(evento.data_lancamento), '%d%m%Y'),
                    'amount': valor,
                    'partner_name': evento.cedente_nome,
                    'ref': evento.numero_documento,
                    'unique_import_id': str(evento.servico_numero_registro),
                })
        header = arquivo.lotes[0].header
        trailer = arquivo.lotes[0].trailer

        inicio = datetime.strptime(str(header.data_saldo_inicial), '%d%m%Y')
        final = datetime.strptime(str(trailer.data_saldo_final), '%d%m%Y')

        vals_bank_statement = {
            'name': u"%s - %s até %s" % (
                arquivo.header.nome_do_banco,
                inicio.strftime('%d/%m/%Y'),
                final.strftime('%d/%m/%Y')),
            'date': inicio,
            'balance_start': arquivo.lotes[0].header.valor_saldo_inicial,
            'balance_end_real': arquivo.lotes[0].trailer.valor_saldo_final,
            'transactions': transacoes
        }
        account_number = str(arquivo.header.cedente_conta)
        if self.force_journal_account:
            account_number = self.journal_id.bank_acc_number
        return (
            arquivo.lotes[0].header.moeda,
            account_number,
            [vals_bank_statement]
        )
