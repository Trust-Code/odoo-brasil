# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models
from odoo.exceptions import UserError


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
