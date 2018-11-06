# -*- coding: utf-8 -*-
# © 2016 Alessandro Fernandes Martini, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import base64
from ..febraban.cnab import Cnab
from datetime import datetime, date
from odoo import api, fields, models
from odoo.exceptions import UserError


class PaymentOrder(models.Model):
    _inherit = 'payment.order'

    cnab_file = fields.Binary('CNAB File', readonly=True)
    file_number = fields.Integer(u'Número sequencial do arquivo', readonly=1)
    data_emissao_cnab = fields.Datetime('Data de Emissão do CNAB')

    @api.multi
    def gerar_cnab(self):
        if len(self.line_ids) < 1:
            raise UserError(
                u'Ordem de Cobrança não possui Linhas de Cobrança!')
        self.data_emissao_cnab = datetime.now()
        self.file_number = self.env['ir.sequence'].next_by_code('cnab.nsa')
        for order_id in self:
            if order_id.line_ids.filtered(
               lambda x: x.state in ('processed', 'rejected', 'paid')):
                raise UserError('Arquivo já enviado e processado pelo banco!')

            cnab = Cnab.get_cnab(
                order_id.src_bank_account_id.bank_bic, '240')()
            remessa = cnab.remessa(order_id)
            order_id.line_ids.write({'state': 'sent'})

            self.name = self.env['ir.sequence'].next_by_code('seq.boleto.name')
            self.cnab_file = base64.b64encode(remessa.encode('UTF-8'))

            self.env['ir.attachment'].create({
                'name': self.name,
                'datas': self.cnab_file,
                'datas_fname': self.name,
                'description': 'Arquivo CNAB 240',
                'res_model': 'payment.order',
                'res_id': order_id
            })


class PaymentOrderLine(models.Model):
    _inherit = 'payment.order.line'

    def mark_order_line_processed(self, cnab_code, cnab_message,
                                  rejected=False, statement_id=None):
        if self.type != 'receivable':
            return super(PaymentOrderLine, self).mark_order_line_processed(
                cnab_code, cnab_message, rejected, statement_id)

        state = 'processed'
        if rejected:
            state = 'rejected'

        self.write({
            'state': state, 'cnab_code': cnab_code,
            'cnab_message': cnab_message
        })
        if not statement_id:
            statement_id = self.env['l10n_br.payment.statement'].create({
                'name': '0001/Manual',
                'date': date.today(),
                'state': 'validated',
            })
        for item in self:
            self.env['l10n_br.payment.statement.line'].create({
                'statement_id': statement_id.id,
                'date': date.today(),
                'name': item.name,
                'partner_id': item.partner_id.id,
                'amount': item.amount_total,
                'cnab_code': cnab_code,
                'cnab_message': cnab_message,
            })
        return statement_id

    def create_receivable_move_and_reconcile(self, order_line):
        move = self.env['account.move'].create({
            'name': '/',
            'journal_id': order_line.journal_id.id,
            'company_id': order_line.journal_id.company_id.id,
            'date': date.today(),
            'ref': order_line.name,
        })
        aml_obj = self.env['account.move.line'].with_context(
            check_move_validity=False)
        counterpart_aml_dict = {
            'name': order_line.name,
            'move_id': move.id,
            'partner_id': order_line.partner_id.id,
            'debit': 0.0,
            'credit': order_line.amount_total,
            'currency_id': order_line.currency_id.id,
            'account_id': order_line.move_line_id.account_id.id,
        }
        liquidity_aml_dict = {
            'name': order_line.name,
            'move_id': move.id,
            'partner_id': order_line.partner_id.id,
            'debit': order_line.amount_total,
            'credit': 0.0,
            'currency_id': order_line.currency_id.id,
            'account_id': order_line.journal_id.default_debit_account_id.id,
        }
        counterpart_aml = aml_obj.create(counterpart_aml_dict)
        aml_obj.create(liquidity_aml_dict)
        move.post()
        (counterpart_aml + order_line.move_line_id).reconcile()
        return move

    def mark_order_line_paid(self, cnab_code, cnab_message, statement_id=None):
        if self.type != 'receivable':
            return super(PaymentOrderLine, self).mark_order_line_paid(
                cnab_code, cnab_message, statement_id)

        bank_account_ids = self.mapped('src_bank_account_id')
        for account in bank_account_ids:
            order_lines = self.filtered(
                lambda x: x.src_bank_account_id == account)
            journal_id = self.env['account.journal'].search(
                [('bank_account_id', '=', account.id)], limit=1)
            if not statement_id:
                statement_id = self.env['l10n_br.payment.statement'].create({
                    'name':
                    journal_id.l10n_br_sequence_statements.next_by_id(),
                    'date': date.today(),
                    'state': 'validated',
                    'journal_id': journal_id.id,
                })
            for item in order_lines:
                move_id = self.create_receivable_move_and_reconcile(item)
                self.env['l10n_br.payment.statement.line'].create({
                    'statement_id': statement_id.id,
                    'date': date.today(),
                    'name': item.name,
                    'partner_id': item.partner_id.id,
                    'amount': item.amount_total,
                    'move_id': move_id.id,
                    'cnab_code': cnab_code,
                    'cnab_message': cnab_message,
                })
            order_lines.write({'state': 'paid'})
