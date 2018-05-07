# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import io
import logging


from odoo import fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

try:
    from ofxparse import OfxParser
except ImportError:
    _logger.debug('Cannot import ofxparse dependencies.')


class AccountBankStatementImport(models.TransientModel):
    _inherit = 'account.bank.statement.import'

    force_format = fields.Boolean(string=u'Forçar formato', default=False)
    file_format = fields.Selection([('ofx', 'Extrato OFX')],
                                   string="Formato do Arquivo",
                                   default='ofx')
    force_journal_account = fields.Boolean(string=u"Forçar conta bancária?")
    journal_id = fields.Many2one('account.journal', string=u"Conta Bancária",
                                 domain=[('type', '=', 'bank')])

    def _parse_file(self, data_file):
        if self.force_format:
            self._check_ofx(data_file, raise_error=True)
            return self._parse_ofx(data_file)
        else:
            if self._check_ofx(data_file):
                return self._parse_ofx(data_file)
            return super(AccountBankStatementImport, self)._parse_file(
                data_file)

    def _check_ofx(self, data_file, raise_error=False):
        try:
            OfxParser.parse(io.BytesIO(data_file))
            return True
        except Exception as e:
            if raise_error:
                raise UserError(u"Arquivo formato inválido:\n%s" % str(e))
            return False

    def _parse_ofx(self, data_file):
        ofx = OfxParser.parse(io.BytesIO(data_file))
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
            'balance_start': float(ofx.account.statement.balance),
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
