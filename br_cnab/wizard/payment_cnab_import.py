# © 2017 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from io import StringIO
from datetime import date, datetime

from odoo import models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

try:
    from cnab240 import get_bank, parse_cnab_code
    from cnab240.tipos import Arquivo
except ImportError:
    _logger.error('Cannot import cnab240 cobranca', exc_info=True)


class l10nBrPaymentCnabImport(models.TransientModel):
    _inherit = 'l10n_br.payment.cnab.import'

    def _get_account(self, cnab_file):
        if self.cnab_type != 'receivable':
            return super(l10nBrPaymentCnabImport, self)._get_account(cnab_file)

        stream = StringIO(cnab_file.decode('ascii'))
        bank = get_bank(self.journal_id.bank_id.bic)
        cnab = Arquivo(bank, arquivo=stream)
        return cnab.header.cedente_conta, cnab.header.cedente_agencia

    def _create_ignored_line(self, statement, vals, payment_line=None):
        name = "%s - %s" % (vals['numero_documento'], vals['sacado_nome'])
        if payment_line:
            name = payment_line.name

        self.env['l10n_br.payment.statement.line'].sudo().create({
            'date': vals['vencimento_titulo'],
            'effective_date': vals['data_ocorrencia'],
            'nosso_numero': vals['nosso_numero'],
            'name': name,
            'amount': vals['titulo_pago'],
            'amount_fee': vals['titulo_acrescimos'],
            'discount': vals['titulo_desconto'],
            'original_amount': vals['valor_titulo'],
            'bank_fee': vals['valor_tarifas'],
            'cnab_code': vals['cnab_code'],
            'cnab_message': vals['cnab_message'],
            'statement_id': statement.id,
            'ignored': True,
            'partner_id': payment_line and payment_line.partner_id.id,
            'move_id': payment_line and payment_line.move_id.id,
        })

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

                if not statement:
                    statement = self.env['l10n_br.payment.statement'].create({
                        'journal_id': self.journal_id.id,
                        'date': date.today(),
                        'company_id': self.journal_id.company_id.id,
                        'name': sequence.next_by_id(),
                        'type': 'receivable',
                    })

                code, message = parse_cnab_code(
                    self.journal_id.bank_id.bic,
                    evento.servico_codigo_movimento)

                payment_line = self.env['payment.order.line'].search(
                    [('nosso_numero', '=', int(evento.nosso_numero)),
                     ('src_bank_account_id', '=',
                      self.journal_id.bank_account_id.id)])

                due_date = date.today()
                effective_date = None
                if evento.vencimento_titulo:
                    due_date = datetime.strptime(
                        "{:08}".format(evento.vencimento_titulo), "%d%m%Y")
                if evento.data_ocorrencia:
                    effective_date = datetime.strptime(
                        "{:08}".format(evento.data_ocorrencia), "%d%m%Y")

                vals = {
                    'nosso_numero': evento.nosso_numero,
                    'numero_documento': evento.numero_documento,
                    'sacado_nome': evento.sacado_nome,
                    'valor_titulo': evento.valor_titulo,
                    'titulo_acrescimos': evento.titulo_acrescimos,
                    'titulo_desconto': evento.titulo_desconto,
                    'titulo_abatimento': evento.titulo_abatimento,
                    'titulo_pago': evento.titulo_pago,
                    'valor_tarifas': evento.valor_tarifas,
                    'titulo_liquido': evento.titulo_liquido,
                    'vencimento_titulo': due_date,
                    'data_ocorrencia': effective_date,
                    'cnab_code': code,
                    'cnab_message': message,
                }

                IMMUTABLE_STATES = ('paid', 'rejected', 'cancelled')
                if payment_line and payment_line.state in IMMUTABLE_STATES:
                    vals['cnab_message'] = 'Importado previamente'
                    self._create_ignored_line(statement, vals, payment_line)
                    continue

                if not payment_line:
                    self._create_ignored_line(statement, vals)
                    continue

                # Process the line
                payment_line.process_receivable_line(statement, vals)

        if not statement:
            raise UserError('Nenhum registro localizado nesse extrato!')
        action = self.env.ref(
            'br_account_payment.action_payment_statement_tree')
        return action.read()[0]
