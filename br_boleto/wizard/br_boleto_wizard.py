# -*- coding: utf-8 -*-
# © 2016 Alessandro Fernandes Martini, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from datetime import date
from odoo import api, fields, models
from odoo.exceptions import UserError


class BrBoletoWizard(models.TransientModel):
    _name = 'br.boleto.wizard'

    payment_due = fields.Boolean(string="Pagamento Atrasado?")
    date_change = fields.Date(string='Alterar Vencimento')
    move_line_id = fields.Many2one('account.move.line', readonly=1)

    @api.multi
    def imprimir_boleto(self):
        line_id = self.move_line_id.l10n_br_order_line_id
        if self.date_change:
            if line_id.state == 'draft':
                self.move_line_id.date_maturity = self.date_change
                line_id.write({
                    'emission_date': date.today(),
                    'date_maturity': self.date_change,
                })
            elif line_id.state != 'cancelled':
                raise UserError(
                    'O boleto está na situação %s, cancele o item de \
                    cobrança antes de reemitir outro boleto' %
                    dict(line_id._fields['state'].selection).get(
                        line_id.state))

        if not line_id or line_id.state in ('rejected', 'cancelled'):
            if self.date_change:
                self.move_line_id.date_maturity = self.date_change
            line_id = self.env['payment.order.line'].action_register_boleto(
                self.move_line_id)

        return self.env.ref(
            'br_boleto.action_boleto_payment_order_line').report_action(
                line_id)
