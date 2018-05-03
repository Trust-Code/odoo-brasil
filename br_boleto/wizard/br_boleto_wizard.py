# -*- coding: utf-8 -*-
# © 2016 Alessandro Fernandes Martini, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models
from odoo.exceptions import UserError

class BrBoletoWizard(models.TransientModel):
    _name = 'br.boleto.wizard'

    payment_due = fields.Boolean(string="Pagamento Atrasado?")
    date_change = fields.Date(string='Alterar Vencimento')
    move_line_id = fields.Many2one('account.move.line', readonly=1)

    @api.multi
    def imprimir_boleto(self):
        if self.move_line_id.payment_mode_id.payment_method != 'boleto':
            raise UserError(
                u'O método de pagamento definido é diferente de boleto!')
        if self.date_change:
            self.move_line_id.date_maturity = self.date_change
            self.move_line_id.boleto_emitido = False

        return self.env.ref(
            'br_boleto.action_boleto_account_move_line').report_action(
                self.move_line_id)
