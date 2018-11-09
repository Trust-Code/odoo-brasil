# © 2017 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from io import StringIO
from datetime import date

from odoo import models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

try:
    from cnab240 import get_bank, parse_cnab_code
    from cnab240.tipos import Arquivo
except ImportError:
    _logger.warning('Cannot import cnab240 cobranca')


class l10nBrPaymentCnabImport(models.TransientModel):
    _inherit = 'l10n_br.payment.cnab.import'

    def _get_account(self, cnab_file):
        if self.cnab_type != 'receivable':
            return super(l10nBrPaymentCnabImport, self)._get_account(cnab_file)

        stream = StringIO(cnab_file.decode('ascii'))
        bank = get_bank(self.journal_id.bank_id.bic)
        cnab = Arquivo(bank, arquivo=stream)
        return cnab.header.cedente_conta, cnab.header.cedente_agencia

    def do_import(self, cnab_file):
        if self.cnab_type != 'receivable':
            return super(l10nBrPaymentCnabImport, self).do_import(cnab_file)

        stream = StringIO(cnab_file.decode('ascii'))
        bank = get_bank(self.journal_id.bank_id.bic)
        arquivo = Arquivo(bank, arquivo=stream)
        sequence = self.journal_id.l10n_br_sequence_statements
        statement = None

        for lote in arquivo.lotes:
            for evento in lote.eventos:
                payment_line = self.env['payment.order.line'].search(
                    [('nosso_numero', '=', int(evento.nosso_numero)),
                     ('src_bank_account_id', '=',
                      self.journal_id.bank_account_id.id)])
                if not payment_line:
                    continue

                if not statement:
                    statement = self.env['l10n_br.payment.statement'].create({
                        'journal_id': self.journal_id.id,
                        'date': date.today(),
                        'company_id': self.journal_id.company_id.id,
                        'name': sequence.next_by_id(),
                    })
                code, message = parse_cnab_code(
                    self.journal_id.bank_id.bic,
                    evento.servico_codigo_movimento)

                if code == '0000':  # Titulo Liquidado
                    payment_line.mark_order_line_paid(
                        code, message, statement_id=statement
                    )
                elif code == '1111':  # Entrada Confirmada
                    payment_line.mark_order_line_processed(
                        evento.servico_codigo_movimento, message,
                        statement_id=statement
                    )
                elif code == '2222':   # Título baixado
                    # TODO Implementar esse caso
                    pass
                elif code == '3333':   # Entrada Rejeitada
                    payment_line.mark_order_line_processed(
                        code, message, rejected=True,
                        statement_id=statement,
                    )

        if not statement:
            raise UserError('Nenhum registro localizado nesse extrato!')
        action = self.env.ref(
            'br_account_payment.action_payment_statement_tree')
        return action.read()[0]
