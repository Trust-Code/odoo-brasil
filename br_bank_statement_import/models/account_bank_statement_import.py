# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
import tempfile
import StringIO

from datetime import datetime
from odoo import fields, models
from odoo.exceptions import UserError
from decimal import Decimal
_logger = logging.getLogger(__name__)

try:
    from cnab240.bancos import sicoob
    from cnab240.bancos import itau
    from cnab240.bancos import bradesco
    from cnab240.bancos import hsbc
    from cnab240.bancos import cef
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
    # determin bank with codes
    # considering 1st 3 chars of header are bank code
    def determine_bank(self, code):
        if code == '341':
            return itau
        elif code == '237':
            return bradesco
        elif code == '104':
            return cef
        elif code == '756':
            return sicoob
        else:
            raise UserError(u'Bank Not supported')

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
            arquivo = open(cnab240_file.name, 'r')
            # read 1st 3 chars of 1st line from file
            bank_code =  arquivo.readline()[0:3]
            bank = self.determine_bank(bank_code)
            Arquivo(bank, arquivo=open(cnab240_file.name, 'r'))
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
        # data file is string here
        bank_code = data_file[0:3]
        bank = self.determine_bank(bank_code)
        cnab240_file.flush()

        arquivo = Arquivo(bank, arquivo=open(cnab240_file.name, 'r'))
        transacoes = []
        total_amt = Decimal(0.00)
        for lote in arquivo.lotes:

            if bank != itau:
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
                name = u"%s - %s até %s" % (
                    arquivo.header.nome_do_banco,
                    inicio.strftime('%d/%m/%Y'),
                    final.strftime('%d/%m/%Y')),
                start_date = inicio
                balance_start = arquivo.lotes[0].header.valor_saldo_inicial
                balance_end_real = arquivo.lotes[0].trailer.valor_saldo_final
            if bank == itau:
                for evento in lote.eventos:
                    if evento.servico_segmento == 'T':
                        transacoes.append({
                            'name': evento.sacado_nome,
                            'date': datetime.strptime(
                                str(evento.vencimento_titulo).zfill(8), '%d%m%Y').date(),
                            'amount': evento.valor_titulo,
                            'ref': evento.numero_documento,
                            'label': evento.sacado_inscricao_numero,  # cnpj
                            'transaction_id': evento.numero_documento,
                            # nosso numero, Alfanumérico
                            'unique_import_id': str(arquivo.header.arquivo_sequencia) + '-' + str(
                                evento.numero_documento),
                            'servico_codigo_movimento': evento.servico_codigo_movimento,
                            'errors': evento.motivo_ocorrencia  # 214-221
                        })
                    else:
                        # set amount and data_ocorrencia from segment U, it has with juros
                        # Formula:
                        # amount = base_value + interest - (discount + rebate)
                        base_value = transacoes[-1]['amount']
                        interest = evento.titulo_acrescimos
                        discount = evento.titulo_desconto
                        rebate = evento.titulo_abatimento
                        if evento.servico_segmento == 'U':
                            transacoes[-1]['amount'] = base_value + interest - (discount + rebate)
                            # replace vencimento with data_ocorrencia
                            transacoes[-1]['date'] = datetime.strptime(
                                str(evento.data_ocorrencia).zfill(8), '%d%m%Y')
                total_amt += evento.titulo_liquido
                name = u'%s - %s' % (arquivo.header.nome_do_banco,
                                 arquivo.header.arquivo_data_de_geracao)
                start_date = datetime.strptime(
                str(arquivo.header.arquivo_data_de_geracao).zfill(8), '%d%m%Y')
                balance_start = 0.0
                balance_end_real = total_amt
        vals_bank_statement = {
            'name': name,
            'date': start_date,
            'balance_start': balance_start,
            'balance_end_real': balance_end_real,
            'transactions': transacoes,
            'currency_code': u'BRL',
            'account_number': arquivo.header.cedente_conta,
        }
        account_number = str(arquivo.header.cedente_conta)
        if self.force_journal_account:
            account_number = self.journal_id.bank_acc_number
        return (
            u'BRL',
            account_number,
            [vals_bank_statement]
        )
