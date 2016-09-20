# -*- coding: utf-8 -*-
# © 2016 Alessandro Fernandes Martini, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class PaymentOrder(models.Model):
    _name = 'payment.order'

    name = fields.Char(max_length=30, string="Nome", required=True)
    user_id = fields.Many2one('res.users', string='Responsável',
                              required=True)
    payment_mode_id = fields.Many2one('payment.mode',
                                      string='Modo de Pagamento',
                                      required=True)
    state = fields.Selection([('draft', 'Rascunho'), ('cancel', 'Canceledo'),
                              ('open', 'Confirmado'), ('done', 'Fechado')])
    line_ids = fields.One2many('account.move.line', 'payment_order_id',
                               required=True, string=u'Linhas de Cobrança')
    currency_id = fields.Many2one('res.currency', string='Moeda')
