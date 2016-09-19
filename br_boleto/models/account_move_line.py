# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models
from odoo.exceptions import UserError
from ..boleto.document import Boleto


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    payment_mode_id = fields.Many2one(
        'payment.mode', string=u"Modo de pagamento")
    boleto_emitido = fields.Boolean(string=u"Emitido")
    nosso_numero = fields.Char(string=u"Nosso número", size=30)

    @api.multi
    def action_register_boleto(self):
        boleto_list = []
        for move in self:
            if not move.company_id.nosso_numero_sequence.id:
                raise UserError('Ação Bloqueada\nCadastre a sequência do nosso \
número nas configurações da companhia')
            if not move.boleto_emitido:
                move.nosso_numero = \
                    move.company_id.nosso_numero_sequence.next_by_id()

            boleto = Boleto.getBoleto(move, move.nosso_numero)
            boleto_list.append(boleto.boleto)
        return boleto_list

    @api.multi
    def action_generate_boleto(self):
        return({
            'name': 'Alterar / Reinprimir Boleto',
            'type': 'ir.actions.act_window',
            'res_model': 'br.boleto.wizard',
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_date_change': fields.Date.context_today(self),
                        'default_invoice_id': self.invoice_id.id}
        })
