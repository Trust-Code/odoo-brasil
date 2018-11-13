# © 2018 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models
from odoo.exceptions import UserError
from ..boleto.document import Boleto


class PaymentOrderLine(models.Model):
    _inherit = 'payment.order.line'

    def generate_payment_order_line(self, move_line):
        """Gera um objeto de payment.order ao imprimir um boleto"""
        order_name = self.env['ir.sequence'].next_by_code('payment.order')
        payment_mode = move_line.payment_mode_id
        payment_order = self.env['payment.order'].search([
            ('state', '=', 'draft'),
            ('payment_mode_id', '=', payment_mode.id)], limit=1)
        order_dict = {
            'name': u'%s' % order_name,
            'user_id': self.env.user.id,
            'payment_mode_id': move_line.payment_mode_id.id,
            'state': 'draft',
            'currency_id': move_line.company_currency_id.id,
            'company_id': payment_mode.journal_id.company_id.id,
            'src_bank_account_id': payment_mode.journal_id.bank_account_id.id,
        }
        if not payment_order:
            payment_order = payment_order.create(order_dict)

        move = self.env['payment.order.line'].search(
            [('src_bank_account_id', '=',
              payment_mode.journal_id.bank_account_id.id),
             ('move_line_id', '=', move_line.id)])
        if not move:
            return self.env['payment.order.line'].create({
                'move_line_id': move_line.id,
                'src_bank_account_id':
                payment_mode.journal_id.bank_account_id.id,
                'journal_id': payment_mode.journal_id.id,
                'payment_order_id': payment_order.id,
                'payment_mode_id': move_line.payment_mode_id.id,
                'date_maturity': move_line.date_maturity,
                'partner_id': move_line.partner_id.id,
                'emission_date': move_line.date,
                'amount_total': move_line.amount_residual,
                'name': "%s/%s" % (move_line.move_id.name, move_line.name),
                'nosso_numero':
                payment_mode.nosso_numero_sequence.next_by_id(),
            })
        return move

    def action_register_boleto(self, move_lines):
        for item in move_lines:
            if item.payment_mode_id.type != 'receivable':
                raise UserError('Modo de pagamento não é boleto!')
            if not item.payment_mode_id.boleto:
                raise UserError('Modo de pagamento não é boleto!')
        for move_line in move_lines:
            order_line = self.generate_payment_order_line(move_line)
            move_line.write({'l10n_br_order_line_id': order_line.id})
            self |= order_line
        move_lines.write({'boleto_emitido': True})
        return self

    def generate_boleto_list(self):
        boleto_list = []
        for line in self:
            boleto = Boleto.getBoleto(line, line.nosso_numero)
            boleto_list.append(boleto.boleto)
        return boleto_list

    def action_print_boleto(self):
        for item in self:
            if item.payment_mode_id.type != 'receivable':
                raise UserError('Modo de pagamento não é boleto!')
            if not item.payment_mode_id.boleto:
                raise UserError('Modo de pagamento não é boleto!')
        return self.env.ref(
            'br_boleto.action_boleto_payment_order_line').report_action(self)
