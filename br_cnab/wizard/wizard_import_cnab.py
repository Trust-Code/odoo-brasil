# -*- coding: utf-8 -*-
# © 2017 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import base64
import tempfile
import logging
import re

from decimal import Decimal
from datetime import datetime

from odoo import fields, models, api
from odoo.exceptions import UserError
from odoo.addons.base.res.res_bank import sanitize_account_number

_logger = logging.getLogger(__name__)

try:
    from cnab240.tipos import Arquivo
except ImportError:
    _logger.debug('Cannot import cnab240 dependencies.')


class WizardImportCnab(models.TransientModel):
    _name = 'wizard.import.cnab'

    cnab_file = fields.Binary(string='Arquivo',
                              help='Arquivo de retorno do tipo CNAB 240')

    journal_id = fields.Many2one(
        'account.journal', string=u"Diário Contábil",
        help=u"Diário Contábil a ser utilizado na importação do CNAB.",
        default="default_get", readonly=False)

    cnab_preview = fields.Html(string='Resumo da importação', readonly=True)

    @api.model
    def default_get(self, fields):
        res = super(WizardImportCnab, self).default_get(fields)
        try:
            res.update({'journal_id': self.env.context['journal_id']})
        except Exception:
            res.update({'journal_id': False})
        return res

    def _create_arquivo_cnab(self, cnab_file):
        cnab_file = base64.b64decode(cnab_file)
        cnab240_file = tempfile.NamedTemporaryFile()
        cnab240_file.write(cnab_file)
        cnab240_file.flush()

        bank = self.get_bank()
        return Arquivo(bank, arquivo=open(cnab240_file.name, 'r'))

    @api.onchange('cnab_file', 'journal_id')
    def _preview_cnab(self):
        codigos_movimentacao = {
            0: u'Evento Desconhecido',
            2: u'Entrada Confirmada',
            3: u'Entrada Rejeitada',
            6: u'Liquidação',
            9: u'Baixa',
            17: u'Liquidação após baixa',
        }
        if self.cnab_file:
            try:
                arquivo = self._create_arquivo_cnab(self.cnab_file)
                lines = []
                for lote in arquivo.lotes:
                    for evento in lote.eventos:
                        nosso_numero = self._get_nosso_numero(
                            evento.nosso_numero)
                        codigo = int(evento.servico_codigo_movimento)
                        lines.append((nosso_numero, codigo,
                                      evento.valor_lancamento))

                preview = '<h3 class="text-center">%s</h3>' % arquivo.\
                    header.nome_do_banco
                preview += '<div style="overflow: scroll; max-height: 300px;">'
                preview += '<table class="table table-striped">'
                preview += '<thead><tr>'
                preview += '<th scope="col">Nosso Numero</th>'
                preview += '<th scope="col">Evento</th>'
                preview += '<th scope="col">Valor</th>'
                preview += '</tr></thead>'
                preview += '<tbody>'

                for line in lines:
                    try:
                        evento = codigos_movimentacao[line[1]]
                    except KeyError:
                        evento = codigos_movimentacao[0]
                    preview += '<tr><td scope="row">%d</td>' % line[0]
                    preview += '<td>%s</td>' % evento
                    preview += '<td>%.2f</td></tr>' % line[2]
                preview += '</tbody></table></div>'

                self.cnab_preview = preview

            except Exception:
                self.cnab_preview = ''
        else:
            self.cnab_preview = ''

    def _get_nosso_numero(self, nosso_numero):
        # TODO Quando outros bancos modificar aqui

        bank = self.journal_id.bank_id.bic

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

    def get_bank(self):
        bank = self.journal_id.bank_id.bic

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

    def _prepare_statement_data(self, arquivo,
                                transactions, move_lines):
        inicio = final = datetime.now()
        valor_total = Decimal('0.0')
        if len(transactions):
            for transaction in transactions:
                valor_total += transaction['amount']

            last_bank_stmt = self.env['account.bank.statement'].search(
                [('journal_id', '=', self.journal_id.id)],
                order="date desc, id desc", limit=1)

            try:
                last_balance = last_bank_stmt[0].balance_end
            except IndexError:
                last_balance = 0.0

            vals_bank_statement = {
                'name': u"%s - %s até %s" % (
                    arquivo.header.nome_do_banco,
                    inicio.strftime('%d/%m/%Y'),
                    final.strftime('%d/%m/%Y')),
                'date': inicio,
                'balance_start': last_balance,
                'balance_end_real': Decimal(last_balance) + valor_total,
                'transactions': transactions,
                'journal_id': self.journal_id.id,
            }

            datas = []
            for line in move_lines:
                datas.append({
                    u'payment_aml_ids': [],
                    u'new_aml_dicts': [],
                    u'counterpart_aml_dicts': [{
                        u'credit': line.debit,
                        u'counterpart_aml_id': line.id,
                        u'name': str(line.move_id.name) + ': ' + str(
                            line.name),
                        u'debit': 0,
                        u'payment_mode_id': line.payment_mode_id.id,
                        u'nosso_numero': line.nosso_numero}]
                    })
            return vals_bank_statement, datas

    def _create_statement(self, stmt_values, account_number):
        BankStatement = self.env['account.bank.statement']
        BankStatementLine = self.env['account.bank.statement.line']
        filtered_values = []
        for transaction in stmt_values['transactions']:
            if 'unique_import_id' not in transaction \
                or not transaction['unique_import_id'] \
                or not bool(BankStatementLine.sudo().search([
                    ('unique_import_id', '=', transaction['unique_import_id'])
                    ], limit=1)):
                if transaction['amount'] != 0:
                    sanitized_account_number = sanitize_account_number(
                        account_number)

                    transaction['unique_import_id'] = (
                        sanitized_account_number and sanitized_account_number +
                        '-' or '') + str(self.journal_id.id) + '-' +\
                        transaction['unique_import_id']

                    partner_bank = self.env['res.partner.bank'].search([
                        ('acc_number', '=', sanitized_account_number)],
                        limit=1)

                    transaction['bank_account_id'] = partner_bank.id

                    filtered_values.append(transaction)

        if len(filtered_values) > 0:
            stmt_values.pop('transactions', None)
            stmt_values['line_ids'] = [
                [0, False, line] for line in filtered_values]

        return BankStatement.create(stmt_values)

    def _get_order_line(self, nosso_numero, method):
        payment_modes = self.env['payment.mode'].search([])

        filtered_pm = payment_modes.filtered(
            lambda x: x.bank_account_id.bank_id ==
            self.journal_id.bank_id
        )

        return self.env[method].search([
            ('nosso_numero', '=', nosso_numero),
            ('payment_mode_id', 'in', filtered_pm.ids)], limit=1)

    def _change_boleto_state(self, evento):
        nosso_numero = self._get_nosso_numero(evento.nosso_numero)

        payment_order_lines = self._get_order_line(
            nosso_numero, 'payment.order.line')

        for line in payment_order_lines:
            if line.state == 'draft':
                if evento.servico_codigo_movimento in (2, '02'):
                    line.write({'state': 'open'})
                if evento.servico_codigo_movimento in (3, '03'):
                    line.write({'state': 'rejected'})
            if evento.servico_codigo_movimento in (9, '09'):
                line.write({'state': 'baixa'})
        return [line.id for line in payment_order_lines]

    def _liquidacao_cnab(self, arquivo, evento, valor):
        nosso_numero = self._get_nosso_numero(evento.nosso_numero)

        move_line = self._get_order_line(nosso_numero, 'account.move.line')
        payment_order_lines = self._get_order_line(
            nosso_numero, 'payment.order.line')
        transaction = {
            'name': "%s : %s" % (
                move_line.partner_id.name or evento.sacado_nome,
                evento.numero_documento or "%s: %s" % (
                    move_line.move_id.name, move_line.name)),
            'amount': valor,

            'partner_name':
            move_line.partner_id.name or evento.sacado_nome,
            'partner_id': move_line.partner_id.id,
            'ref': evento.numero_documento,
            'unique_import_id': str(evento.nosso_numero),
            'nosso_numero': nosso_numero,
            'bank_account_id': move_line.payment_mode_id.bank_account_id.id
        }

        return transaction, move_line, payment_order_lines.ids

    def _parse_cnab(self, cnab_file):
        arquivo = self._create_arquivo_cnab(cnab_file)
        transactions = []
        move_lines = []
        payment_line_ids = []
        for lote in arquivo.lotes:
            for evento in lote.eventos:
                valor = evento.valor_lancamento

                if evento.servico_codigo_movimento in (6, 17, '06', '17',):
                    transaction, move_line, pay_lines = self._liquidacao_cnab(
                        arquivo, evento, valor)

                    transactions.append(transaction)
                    move_lines.append(move_line)
                    for item in pay_lines:
                        payment_line_ids.append(item)

                elif evento.servico_codigo_movimento in (2, 3, 9,
                                                         '02', '03', '09'):
                    pay_lines = self._change_boleto_state(evento)
                    for item in pay_lines:
                        payment_line_ids.append(item)

        return arquivo, transactions, move_lines, payment_line_ids

    def _check_cnab(self, cnab_file):
        if int(base64.b64decode(cnab_file)[0:3]) != int(
                self.journal_id.bank_id.bic):
            raise UserError(u"O banco do arquivo não corresponde ao\
                banco do Diário Contábil!")

        try:
            arquivo = self._create_arquivo_cnab(cnab_file)
        except Exception:
            raise UserError(u"Formato de arquivo inválido!")

        if not arquivo.lotes:
            raise UserError(u"O arquivo não contém nenhum lote!")

        for lote in arquivo.lotes:
            nao_contem_eventos = True
            if lote.eventos:
                nao_contem_eventos = False
            if nao_contem_eventos:
                raise UserError(u"O arquivo não contém nenhum evento!")
        cnpj = self.journal_id.company_id.cnpj_cpf
        cnpj = re.sub('[^0-9]', '', cnpj)
        if not int(cnpj) == arquivo.header.cedente_inscricao_numero:
            raise UserError(u"Este arquivo de retorno não pertence à essa\
                empresa, selecione o Diário correto.")

        return True

    def _parse_file(self, cnab_file):
        if self._check_cnab(cnab_file):
            return self._parse_cnab(cnab_file)

    def action_open_payment_lines(self, lines):
        action = self.env.ref('br_boleto.action_payment_order_line_form'
                              ).read()[0]
        if lines:
            action['domain'] = [('id', 'in', lines)]
        return action

    def import_cnab(self):
        arquivo, transactions, move_lines, pay_line_ids = self.with_context(
            active_id=self.ids[0])._parse_file(self.cnab_file)
        if len(transactions) > 0:
            vals_stmt, datas = self._prepare_statement_data(
                arquivo, transactions, move_lines)

            account_number = self.journal_id.bank_acc_number

            statement = self._create_statement(
                vals_stmt, account_number)

            for line, data in zip(statement.line_ids, datas):
                line.process_reconciliations([data])
        return self.action_open_payment_lines(pay_line_ids)


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    def wizard_import_cnab(self):
        action = self.env.ref('br_cnab.action_import_cnab_240')
        return {
            'name': action.name,
            'context': dict(
                self.env.context,
                journal_id=self.id),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'wizard.import.cnab',
            'type': 'ir.actions.act_window',
            'target': 'new'
        }
