# -*- coding: utf-8 -*-
# © 2016 Alessandro Fernandes Martini, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import base64
from ..febraban.cnab import Cnab
from decimal import Decimal
from datetime import datetime
from odoo import api, models
from odoo.exceptions import UserError


class PaymentOrder(models.Model):
    _inherit = 'payment.order'

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

            self.name = self._get_next_code()
            self.cnab_file = base64.b64encode(remessa.encode('UTF-8'))

            self.env['ir.attachment'].create({
                'name': self.name,
                'datas': self.cnab_file,
                'datas_fname': self.name,
                'description': 'Arquivo CNAB 240',
                'res_model': 'payment.order',
                'res_id': order_id
            })


TITULO_LIQUIDADO = '0000'
ENTRADA_CONFIRMADA = '1111'
BAIXA_TITULO = '2222'
ENTRADA_REJEITADA = '3333'


class PaymentOrderLine(models.Model):
    _inherit = 'payment.order.line'

    def process_receivable_line(self, statement_id, cnab_vals):
        self.ensure_one()
        state = message = payment_move = None
        ignored = False
        if cnab_vals['cnab_code'] == TITULO_LIQUIDADO:
            state = 'paid'
            payment_move = self.register_receivable_payment(cnab_vals)

        elif cnab_vals['cnab_code'] == ENTRADA_CONFIRMADA:
            state = 'processed'

        elif cnab_vals['cnab_code'] == BAIXA_TITULO:
            state = 'cancelled'
            message = 'Item cancelado via baixa bancária'

        elif cnab_vals['cnab_code'] == ENTRADA_REJEITADA:   # Entrada Rejeitada
            state = 'rejected'
        else:
            ignored = True

        self.env['l10n_br.payment.statement.line'].sudo().create({
            'statement_id': statement_id.id,
            'name': self.name,
            'partner_id': self.partner_id.id,
            'amount': cnab_vals['titulo_pago'],
            'nosso_numero': self.nosso_numero,
            'date': cnab_vals['vencimento_titulo'],
            'effective_date': cnab_vals['data_ocorrencia'],
            'amount_fee': cnab_vals['titulo_acrescimos'],
            'discount': cnab_vals['titulo_desconto'],
            'original_amount': cnab_vals['valor_titulo'],
            'bank_fee': cnab_vals['valor_tarifas'],
            'cnab_code': cnab_vals['cnab_code'],
            'cnab_message': cnab_vals['cnab_message'],
            'move_id': payment_move and payment_move.id or self.move_id.id,
            'ignored': ignored,
        })
        self.write({
            'state': state,
            'cnab_code': cnab_vals['cnab_code'],
            'cnab_message': message or cnab_vals['cnab_message'],
        })

    def register_receivable_payment(self, cnab_vals):
        self.ensure_one()
        move = self.env['account.move'].create({
            'name': '/',
            'journal_id': self.journal_id.id,
            'company_id': self.journal_id.company_id.id,
            'date': cnab_vals['data_ocorrencia'],
            'ref': self.name,
        })
        aml_obj = self.env['account.move.line'].with_context(
            check_move_validity=False)
        counterpart_aml_dict = {
            'name': self.name,
            'move_id': move.id,
            'partner_id': self.partner_id.id,
            'debit': 0.0,
            'credit': float(cnab_vals['valor_titulo'] -
                            cnab_vals['titulo_desconto']),
            'currency_id': self.currency_id.id,
            'account_id': self.move_line_id.account_id.id,
        }
        liquidity_aml_dict = {
            'name': self.name,
            'move_id': move.id,
            'partner_id': self.partner_id.id,
            'debit': float(
                cnab_vals['valor_titulo'] + cnab_vals['titulo_acrescimos'] -
                cnab_vals['titulo_desconto'] - cnab_vals['valor_tarifas']
                ),
            'credit': 0.0,
            'currency_id': self.currency_id.id,
            'account_id': self.journal_id.default_debit_account_id.id,
        }
        if cnab_vals['titulo_acrescimos'] > Decimal(0):
            account_id = self.journal_id.company_id.l10n_br_interest_account_id
            if not account_id:
                raise UserError(
                    'Configure a conta de recebimento de juros/multa')
            ext_line = {
                'name': 'Título Acréscimos (juros/multa)',
                'move_id': move.id,
                'partner_id': self.partner_id.id,
                'debit': 0.0,
                'credit': float(cnab_vals['titulo_acrescimos']),
                'currency_id': self.currency_id.id,
                'account_id': account_id.id,
            }
            aml_obj.create(ext_line)
        if cnab_vals['valor_tarifas'] > Decimal(0):
            account_id = self.journal_id.company_id.l10n_br_bankfee_account_id
            if not account_id:
                raise UserError(
                    'Configure a conta de tarifas bancárias')
            ext_line = {
                'name': 'Tarifas bancárias (boleto)',
                'move_id': move.id,
                'partner_id': self.partner_id.id,
                'debit': float(cnab_vals['valor_tarifas']),
                'credit': 0.0,
                'currency_id': self.currency_id.id,
                'account_id': account_id.id,
            }
            aml_obj.create(ext_line)

        counterpart_aml = aml_obj.create(counterpart_aml_dict)
        aml_obj.create(liquidity_aml_dict)
        move.post()
        (counterpart_aml + self.move_line_id).reconcile()
        return move
