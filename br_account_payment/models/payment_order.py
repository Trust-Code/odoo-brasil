# -*- coding: utf-8 -*-
# © 2016 Alessandro Fernandes Martini, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models
from odoo.exceptions import UserError


class PaymentOrderLine(models.Model):
    _name = 'payment.order.line'
    _order = 'id desc'
    _description = 'Linha de Pagamento/Cobrança'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    def _compute_identifier(self):
        for item in self:
            item.identifier = "%08d" % item.id

    name = fields.Char(string="Ref.", size=20)
    identifier = fields.Char(
        string="Identificador", compute='_compute_identifier')
    payment_order_id = fields.Many2one(
        'payment.order', string="Ordem de Pagamento", ondelete="restrict")
    src_bank_account_id = fields.Many2one(
        'res.partner.bank', string="Conta Bancária")
    company_id = fields.Many2one(
        'res.company', string="Company",
        related="payment_order_id.company_id", store=True)
    type = fields.Selection(
        [('receivable', 'Recebível'), ('payable', 'Pagável')],
        string="Tipo de Ordem", default='receivable')
    move_line_id = fields.Many2one(
        'account.move.line', string='Item de Diário')
    partner_id = fields.Many2one(
        'res.partner', string="Parceiro", readonly=True)
    journal_id = fields.Many2one('account.journal', string="Diário")
    move_id = fields.Many2one('account.move', string="Lançamento de Diário",
                              related='move_line_id.move_id', readonly=True)
    nosso_numero = fields.Char(string=u"Nosso Número", size=20)
    payment_mode_id = fields.Many2one(
        'l10n_br.payment.mode', string="Modo de pagamento")
    date_maturity = fields.Date(string="Vencimento")
    emission_date = fields.Date(string="Data de Emissão")
    currency_id = fields.Many2one('res.currency', string="Currency")
    amount_total = fields.Monetary(
        string="Valor", digits=(18, 2), oldname='value')
    state = fields.Selection([("draft", "Rascunho"),
                              ("approved", "Aprovado"),
                              ("sent", "Enviado"),
                              ("processed", "Processado"),
                              ("rejected", "Rejeitado"),
                              ("paid", "Pago"),
                              ("cancelled", "Cancelado")],
                             string="Situação",
                             default="draft", track_visibility='onchange')

    @api.multi
    def unlink(self):
        lines = self.filtered(lambda x: x.state != 'draft')
        if lines:
            raise UserError(
                'Apenas pagamentos no estado provisório podem ser excluídos')
        return super(PaymentOrderLine, self).unlink()

    @api.multi
    def action_cancel_line(self):
        self.write({'state': 'cancelled'})


class PaymentOrder(models.Model):
    _name = 'payment.order'
    _order = 'id desc'

    @api.depends('line_ids')
    def _compute_amount_total(self):
        for item in self:
            amount_total = 0
            for line in item.line_ids:
                amount_total += line.amount_total
            item.amount_total = amount_total

    name = fields.Char(max_length=30, string="Nome", required=True)
    company_id = fields.Many2one(
        'res.company', string='Company', required=True, ondelete='restrict',
        default=lambda self: self.env['res.company']._company_default_get(
            'account.l10n_br.payment.mode'))
    type = fields.Selection(
        [('receivable', 'Recebível'), ('payable', 'Pagável')],
        string="Tipo de Ordem", default='receivable')
    user_id = fields.Many2one('res.users', string=u'Responsável',
                              required=True)
    payment_mode_id = fields.Many2one('l10n_br.payment.mode',
                                      string='Modo de Pagamento',
                                      required=True)
    journal_id = fields.Many2one(
        'account.journal', string="Diário")
    src_bank_account_id = fields.Many2one(
        'res.partner.bank', string="Conta Bancária")
    state = fields.Selection(
        [('draft', 'Rascunho'),
         ('open', 'Aberto'),
         ('attention', 'Necessita Atenção'),
         ('done', 'Finalizado')],
        string="Situação",
        compute="_compute_state",
        store=True)
    line_ids = fields.One2many('payment.order.line', 'payment_order_id',
                               required=True, string=u'Linhas de Cobrança')
    currency_id = fields.Many2one('res.currency', string='Moeda')
    amount_total = fields.Float(string="Total",
                                compute='_compute_amount_total')

    def mark_order_line_processed(self, cnab_code, cnab_message,
                                  rejected=False, statement_id=None):
        pass

    def mark_order_line_paid(self, cnab_code, cnab_message, statement_id=None):
        pass

    @api.multi
    @api.depends('line_ids.state')
    def _compute_state(self):
        for item in self:
            lines = item.line_ids.filtered(lambda x: x.state != 'cancelled')
            if all(line.state == 'draft' for line in lines):
                item.state = 'draft'
            elif all(line.state == 'paid' for line in lines):
                item.state = 'done'
            elif any(line.state == 'rejected' for line in lines):
                item.state = 'attention'
            else:
                item.state = 'open'

    @api.multi
    def unlink(self):
        for item in self:
            item.line_ids.unlink()
        return super(PaymentOrder, self).unlink()
