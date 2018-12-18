# © 2017 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from io import StringIO
from datetime import date, datetime

from odoo import models

_logger = logging.getLogger(__name__)

try:
    from pycnab240.file import File
    from pycnab240.utils import get_bank, get_return_message
except ImportError:
    _logger.error('Cannot import pycnab240', exc_info=True)


class l10nBrPaymentCnabImport(models.TransientModel):
    _inherit = 'l10n_br.payment.cnab.import'

    def _get_account(self, cnab_file):
        if self.cnab_type != 'payable':
            return super(l10nBrPaymentCnabImport, self)._get_account(cnab_file)

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

        statement = self.env['l10n_br.payment.statement'].sudo().create({
            'journal_id': self.journal_id.id,
            'date': date.today(),
            'company_id': self.journal_id.company_id.id,
            'name': self.journal_id.l10n_br_sequence_statements.next_by_id(),
            'type': 'payable',
        })
        for lot in loaded_cnab.lots:
            for event in lot.events:
                payment_line = self.env['payment.order.line'].search(
                    [('nosso_numero', '=', event.numero_documento_cliente),
                     ('journal_id', '=', self.journal_id.id),
                     ('type', '=', 'payable')])

                cnab_code = event.ocorrencias_retorno[:2]
                message = self._get_message(
                    self.journal_id.bank_id.bic,
                    event.ocorrencias_retorno.strip())
                if not payment_line:
                    nome = ''
                    if hasattr(event, 'favorecido_nome'):
                        nome = event.favorecido_nome
                    elif hasattr(event, 'nome_concessionaria'):
                        nome = event.nome_concessionaria
                    elif hasattr(event, 'contribuinte_nome'):
                        nome = event.contribuinte_nome

                    self.env['l10n_br.payment.statement.line'].sudo().create({
                        'date': datetime.strptime(
                            "{:08}".format(event.data_pagamento), "%d%m%Y"),
                        'nosso_numero': event.numero_documento_cliente,
                        'name': nome,
                        'amount': event.valor_pagamento,
                        'cnab_code': cnab_code,
                        'cnab_message': message,
                        'statement_id': statement.id,
                        'ignored': True,
                    })
                    continue
                protocol = autentication = None
                if hasattr(event, 'protocolo_pagamento'):
                    protocol = event.protocolo_pagamento
                if hasattr(event, 'autenticacao_pagamento'):
                    autentication = event.autenticacao_pagamento
                self.select_routing(
                    payment_line, cnab_code, bank, message, statement,
                    protocolo=protocol, autenticacao=autentication)

        action = self.env.ref(
            'br_account_payment.action_payment_statement_tree')
        return action.read()[0]

    def select_routing(self, pay_line, cnab_code, bank, message,
                       statement, protocolo=None, autenticacao=None):
        if cnab_code == 'BD':  # Inclusão OK
            pay_line.mark_order_line_processed(
                cnab_code, message, statement_id=statement
            )
        elif cnab_code in ('00', '03'):  # Débito
            pay_line.mark_order_line_paid(
                cnab_code, message, statement_id=statement,
                autenticacao=autenticacao, protocolo=protocolo)
        else:
            pay_line.mark_order_line_processed(
                cnab_code, message, rejected=True,
                statement_id=statement)
