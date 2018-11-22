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
    def unlink(self):
        for item in self:
            line_ids = self.env['payment.order.line'].search(
                [('move_line_id', '=', item.id),
                 ('state', '=', 'draft')])
            line_ids.sudo().unlink()
        return super(AccountMoveLine, self).unlink()

    @api.multi
    def _update_check(self):
        for item in self:
            total = self.env['payment.order.line'].search_count(
                [('move_line_id', '=', item.id),
                 ('type', '=', 'receivable'),
                 ('state', 'not in', ('draft', 'cancelled', 'rejected'))])
            if total > 0:
                raise UserError('Existem boletos emitidos para esta fatura!\
                                Cancele estes boletos primeiro')
        return super(AccountMoveLine, self)._update_check()

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
