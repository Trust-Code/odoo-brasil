# -*- coding: utf-8 -*-
# © 2016 Alessandro Fernandes Martini, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class PaymentOrderLine(models.Model):
    _name = 'payment.order.line'

    name = fields.Char(string="Ref.", size=20)
    payment_order_id = fields.Many2one(
        'payment.order', string="Ordem de Pagamento", ondelete="cascade")
    type = fields.Selection(
        related='payment_order_id.type', readonly=True, store=True)
    move_line_id = fields.Many2one(
        'account.move.line', string=u'Linhas de Cobrança')
    partner_id = fields.Many2one(
        'res.partner', string="Parceiro", readonly=True)
    move_id = fields.Many2one('account.move', string=u"Lançamento de Diário",
                              related='move_line_id.move_id', readonly=True)
    nosso_numero = fields.Char(string=u"Nosso Número", size=20)
    payment_mode_id = fields.Many2one(
        'payment.mode', string="Modo de pagamento")
    date_maturity = fields.Date(string="Vencimento")
    value = fields.Float(string="Valor", digits=(18, 2))
    state = fields.Selection([("draft", "Rascunho"),
                              ("sent", "Enviado"),
                              ("approved", "Aprovado"),
                              ("rejected", "Rejeitado"),
                              ("paid", "Pago")],
                             string=u"Situação",
                             default="draft")


class PaymentOrder(models.Model):
    _name = 'payment.order'
    _order = 'id desc'

    @api.depends('line_ids')
    def _compute_amount_total(self):
        for item in self:
            amount_total = 0
            for line in item.line_ids:
                amount_total += line.value
            item.amount_total = amount_total

    name = fields.Char(max_length=30, string="Nome", required=True)
    type = fields.Selection(
        [('receivable', 'Recebível'), ('payable', 'Pagável')],
        string="Tipo de Ordem", default='receivable')
    user_id = fields.Many2one('res.users', string=u'Responsável',
                              required=True)
    payment_mode_id = fields.Many2one('payment.mode',
                                      string='Modo de Pagamento',
                                      required=True)
    state = fields.Selection(
        [('draft', 'Rascunho'),
         ('sent', 'Enviado'),
         ('approved', 'Aprovado'),
         ('attention', 'Necessita Atenção'),
         ('done', 'Fechado')],
        string=u"Situação",
        compute="_compute_state",
        store=True)
    line_ids = fields.One2many('payment.order.line', 'payment_order_id',
                               required=True, string=u'Linhas de Cobrança')
    currency_id = fields.Many2one('res.currency', string='Moeda')
    amount_total = fields.Float(string="Total",
                                compute='_compute_amount_total')

    @api.multi
    @api.depends('line_ids.state')
    def _compute_state(self):
        for item in self:
            if all(line.state == 'paid' for line in item.line_ids):
                item.state = 'done'
            elif any(line.state == 'rejected' for line in item.line_ids):
                item.state = 'attention'
            elif any(line.state == 'draft' for line in item.line_ids):
                item.state = 'draft'
            elif any(line.state == 'sent' for line in item.line_ids):
                item.state = 'sent'
            elif any(line.state == 'approved' for line in item.line_ids):
                item.state = 'approved'
            else:
                item.state = 'draft'
