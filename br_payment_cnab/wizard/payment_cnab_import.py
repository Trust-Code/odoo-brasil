# © 2017 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from io import StringIO
from datetime import date

from odoo import models

_logger = logging.getLogger(__name__)

try:
    from pycnab240.file import File
    from pycnab240.utils import get_bank, get_return_message
except ImportError:
    _logger.warning('Cannot import pycnab240')


class l10nBrPaymentCnabImport(models.TransientModel):
    _inherit = 'l10n_br.payment.cnab.import'

    def _get_account(self, cnab_file):
        if self.cnab_type != 'payable':
            return super(l10nBrPaymentCnabImport, self).do_import(cnab_file)

        stream = StringIO(cnab_file.decode('ascii'))
        bank = get_bank(self.journal_id.bank_id.bic)
        cnab = File(bank)
        cnab.load_return_file(stream)
        return cnab.header.cedente_conta, cnab.header.cedente_agencia

    def _get_message(self, bank, ocorrencias):
        msgs = get_return_message(bank, ocorrencias[0:2])
        for msg in range(4, int(len(ocorrencias))+1, 2):
            msgs += ' -- ' + get_return_message(bank, ocorrencias[msg-2:msg])
        return msgs

    def do_import(self, cnab_file):
        if self.cnab_type != 'payable':
            return super(l10nBrPaymentCnabImport, self).do_import(cnab_file)

        stream = StringIO(cnab_file.decode('ascii'))
        bank = get_bank(self.journal_id.bank_id.bic)
        account, bra_number = self._get_account(cnab_file)
        loaded_cnab = File(bank)
        loaded_cnab.load_return_file(stream)

        statement = self.env['l10n_br.payment.statement'].create({
            'journal_id': self.journal_id.id,
            'date': date.today(),
            'company_id': self.journal_id.company_id.id,
            'name': self.journal_id.l10n_br_sequence_statements.next_by_id(),
        })
        for lot in loaded_cnab.lots:
            for event in lot.events:
                payment_line = self.env['payment.order.line'].search(
                    [('nosso_numero', '=', event.numero_documento_cliente),
                     ('journal_id', '=', self.journal_id.id),
                     ('type', '=', 'payable')])

                if not payment_line:
                    continue
                cnab_code = event.ocorrencias_retorno[:2]
                message = self._get_message(
                    self.journal_id.bank_id.bic,
                    event.ocorrencias_retorno.strip())
                self.select_routing(
                    payment_line, cnab_code, bank, message, statement)

        action = self.env.ref(
            'br_account_payment.action_payment_statement_tree')
        return action.read()[0]

    def select_routing(self, pay_line, cnab_code, bank, message, statement):
        if cnab_code == 'BD':  # Inclusão OK
            pay_line.mark_order_line_processed(
                cnab_code, message
            )
        elif cnab_code in ('00', '03'):  # Débito
            pay_line.mark_order_line_paid(
                cnab_code, message, statement_id=statement
            )
        else:
            pay_line.mark_order_line_processed(
                cnab_code, message, rejected=True,
                statement_id=statement)
