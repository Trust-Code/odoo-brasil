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
        stream = StringIO(cnab_file.decode('ascii'))
        bank = get_bank(self.journal_id.bank_id.bic)
        cnab = File(bank)
        cnab.load_return_file(stream)
        return cnab.header.cedente_conta, cnab.header.cedente_agencia

    def do_import(self, cnab_file):
        stream = StringIO(cnab_file.decode('ascii'))

        bank = get_bank(self.journal_id.bank_id.bic)
        loaded_cnab = File(bank)
        loaded_cnab.load_return_file(stream)
        self.validate_journal(loaded_cnab)

        statement = self.env['l10n_br.payment.statement'].create({
            'journal_id': self.journal_id.id,
            'date': date.today(),
            'company_id': self.journal_id.company_id.id,
            'name': self.journal_id.l10n_br_sequence_statements.next_by_id(),
        })

        for lot in loaded_cnab.lots:
            for event in lot.events:
                payment_line = self.env['payment.order.line'].search(
                    [('nosso_numero', '=', event.numero_documento_cliente)])

                if not payment_line:
                    continue
                cnab_code = event.ocorrencias_retorno[:2]
                message = get_return_message(
                    self.journal_id.bank_id.bic,
                    event.ocorrencias_retorno.strip()[:2])
                if cnab_code == 'BD':  # Inclusão OK
                    payment_line.mark_order_line_processed(
                        cnab_code, message
                    )
                elif cnab_code in ('01', '03'):  # Débito
                    payment_line.mark_order_line_paid(
                        cnab_code, message, statement_id=statement
                    )
                else:
                    payment_line.mark_order_line_processed(
                        cnab_code, message, rejected=True,
                        statement_id=statement,
                    )

        action = self.env.ref('br_account_payment.action_payment_statement_tree')
        return action.read()[0]
