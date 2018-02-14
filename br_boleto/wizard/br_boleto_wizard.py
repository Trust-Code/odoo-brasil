# -*- coding: utf-8 -*-
# © 2016 Alessandro Fernandes Martini, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class BrBoletoWizard(models.TransientModel):
    _name = 'br.boleto.wizard'

    payment_due = fields.Boolean(string="Pagamento Atrasado?")
    date_change = fields.Date(string='Alterar Vencimento')
    move_line_id = fields.Many2one('account.move.line', readonly=1)

    @api.multi
    def imprimir_boleto(self):
        order_line = self.env['payment.order.line'].search([
            ('move_line_id', '=', self.move_line_id.id)])
        if order_line:
            order_line.unlink()
        if self.date_change:
            self.move_line_id.date_maturity = self.date_change
            self.move_line_id.boleto_emitido = False

        return self.env['report'].get_action(self.move_line_id.id,
                                             'br_boleto.report.print')
