# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import io
import uuid
import logging

from odoo import fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

try:
    from ofxparse import OfxParser
except ImportError:
    _logger.error('Cannot import ofxparse dependencies.', exc_info=True)


class AccountBankStatementImport(models.TransientModel):
    _inherit = 'account.bank.statement.import'

    unique_transaction = fields.Boolean(
        string='Gerar ID Único', default=False,
        help="Apenas marque esta opção em caso do arquivo OFX conter \
        registros duplicados (campo FITID), alguns bancos exportam \
        o arquivo OFX com dois registros diferentes com mesmo número \
        de transação (o que não deveria). O comportamento padrão do Odoo \
        caso exista duplicados é ignorar os duplicados (mesmo FITID) \
        e se forem todos duplicados dizer que o arquivo já foi importado. \
        Se alguma dessas situações estiver ocorrendo ao importar o arquivo \
        talvez você precise marcar esta opção.")
    force_journal_account = fields.Boolean(string=u"Forçar conta bancária?")
    journal_id = fields.Many2one('account.journal', string=u"Conta Bancária",
                                 domain=[('type', '=', 'bank')])

    def _parse_file(self, data_file):
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
                raise UserError(_("Arquivo formato inválido:\n%s") % str(e))
            return False

    def _parse_ofx(self, data_file):
        ofx = OfxParser.parse(io.BytesIO(data_file))
        transacoes = []
        total = 0.0
        for account in ofx.accounts:
            for transacao in account.statement.transactions:
                unique_id = transacao.id
                if self.unique_transaction:
                    unique_id = str(uuid.uuid4())
                transacoes.append({
                    'date': transacao.date,
                    'name': transacao.payee + (
                        transacao.memo and ': ' + transacao.memo or ''),
                    'ref': transacao.id,
                    'amount': transacao.amount,
                    'unique_import_id': unique_id,
                    'sequence': len(transacoes) + 1,
                })
                total += float(transacao.amount)
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
        total = round(total, 2)
        vals_bank_statement = {
            'name': name,
            'transactions': transacoes,
            'balance_start': round(
                float(ofx.account.statement.balance) - total, 2),
            'balance_end_real': round(ofx.account.statement.balance, 2),
        }

        account_number = ofx.account.number
        if self.force_journal_account:
            account_number = self.journal_id.bank_acc_number
        return (
            ofx.account.statement.currency,
            account_number,
            [vals_bank_statement]
        )
