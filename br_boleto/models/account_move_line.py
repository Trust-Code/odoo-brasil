# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from datetime import datetime
from odoo import api, fields, models
from odoo.exceptions import UserError
from ..boleto.document import Boleto


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    boleto_emitido = fields.Boolean(string=u"Emitido")
    nosso_numero = fields.Char(string=u"Nosso Número", size=30)

    @api.multi
    def action_print_boleto(self):
        if self.move_id.state in ('draft', 'cancel'):
            raise UserError(
                u'Fatura provisória ou cancelada não permite emitir boleto')
        self = self.with_context({'origin_model': 'account.invoice'})
        return self.env.ref(
            'br_boleto.action_boleto_account_invoice').report_action(self)

    @api.multi
    def gerar_payment_order(self):
        """Gera um objeto de payment.order ao imprimir um boleto"""
        order_name = self.env['ir.sequence'].next_by_code('payment.order')
        payment_order = self.env['payment.order'].search([
            ('state', '=', 'draft'),
            ('payment_mode_id', '=', self.payment_mode_id.id)], limit=1)
        order_dict = {
            'name': u'%s' % order_name,
            'user_id': self.write_uid.id,
            'payment_mode_id': self.payment_mode_id.id,
            'state': 'draft',
            'currency_id': self.company_currency_id.id,
        }
        if not payment_order:
            payment_order = payment_order.create(order_dict)

        move = self.env['payment.order.line'].search(
            [('payment_mode_id', '=', self.payment_mode_id.id),
             ('nosso_numero', '=', self.nosso_numero)])
        if not move:
            self.env['payment.order.line'].create({
                'move_line_id': self.id,
                'payment_order_id': payment_order.id,
                'nosso_numero': self.nosso_numero,
                'payment_mode_id': self.payment_mode_id.id,
                'date_maturity': self.date_maturity,
                'value': self.amount_residual,
                'name': self.name,
            })

    @api.multi
    def action_register_boleto(self):
        boleto_list = []
        for move in self:
            if not move.payment_mode_id:
                raise UserError(
                    u'O modo de pagamento configurado não é boleto')
            if not move.payment_mode_id.nosso_numero_sequence.id:
                raise UserError(u'Cadastre a sequência do nosso número no modo \
                                de pagamento')
            if not move.boleto_emitido:
                vencimento = fields.Date.from_string(move.date_maturity)
                if vencimento < datetime.today().date() and not\
                        move.reconciled:
                    raise UserError(u'A data de vencimento deve ser maior que a \
                                    data atual na fatura: ' +
                                    move.move_id.name +
                                    u' - ' + move.partner_id.name +
                                    u'.\n Altere a data de vencimento!')
                move.boleto_emitido = True
                move.nosso_numero = \
                    move.payment_mode_id.nosso_numero_sequence.next_by_id()

            boleto = Boleto.getBoleto(move, move.nosso_numero)
            boleto_list.append(boleto.boleto)
            move.gerar_payment_order()
        return boleto_list

    @api.multi
    def open_wizard_print_boleto(self):
        return({
            'name': 'Alterar / Reimprimir Boleto',
            'type': 'ir.actions.act_window',
            'res_model': 'br.boleto.wizard',
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'origin_model': 'account.move.line',
                'default_move_line_id': self.id,
            }
        })
