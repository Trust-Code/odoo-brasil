# -*- coding: utf-8 -*-
# © 2016 Alessandro Fernandes Martini, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    payment_mode_id = fields.Many2one('payment.mode', string="Modo de Pagamento")
    move_line_id = fields.Many2one('account.move.line', string="Linha de fatura")
    total_moves = fields.Integer('Linha(s)', compute='_compute_open_moves')
    payment_difference_move = fields.Monetary(compute='_compute_amount_move', readonly=True)
    amount_move_line = fields.Monetary(compute='_compute_amount_move', readonly=True)
    residual_amount_move_line = fields.Monetary(compute='_compute_amount_move', readonly=True)
    move_number = fields.Char(compute='_compute_amount_move', readonly=True)
    move_all_quota = fields.Char(compute='_compute_amount_move', readonly=True)

    @api.one
    @api.depends('move_line_id.amount_residual','amount')
    def _compute_amount_move(self):
        if len(self.move_line_id) == 0:
            return
        if self.move_line_id.billing_type == '1':
            self.amount_move_line = self.move_line_id.debit
            self.residual_amount_move_line = self.move_line_id.amount_residual
        if self.move_line_id.billing_type == '2':
            self.amount_move_line = self.move_line_id.credit
            self.residual_amount_move_line = self.move_line_id.amount_residual * -1
        self.payment_difference_move = self.residual_amount_move_line - self.amount
        self.move_number = self.move_line_id.name
        self.move_all_quota = self.move_line_id.total_quota_invoice

    @api.onchange('move_line_id')
    def set_amount(self):
        self.amount = self.residual_amount_move_line
        self.payment_mode_id = self.move_line_id.payment_mode_id

    @api.onchange('payment_mode_id')
    def set_journal_id(self):
        self.journal_id = self.payment_mode_id.journal_id

    @api.model
    def default_get(self, fields):
        rec = super(AccountPayment, self).default_get(fields)
        if self.env.context.get('default_move_line_id', False):
            rec['amount'] = self.env.context.get(
                'default_amount', rec.get('amount', 0.0))

        return rec

    def _create_payment_entry(self, amount):
        self = self.with_context(move_line_to_reconcile=self.move_line_id)
        return super(AccountPayment, self)._create_payment_entry(amount)

    @api.depends('partner_id', 'partner_type')
    def _compute_open_moves(self):
        for item in self:
            if item.partner_type == 'supplier':
                account_type = 'payable'
                column = 'debit'
            else:
                account_type = 'receivable'
                column = 'credit'

            item.total_moves = self.env['account.move.line'].search_count(
                [('partner_id', '=', item.partner_id.id),
                 ('user_type_id.type', '=', account_type),
                 (column, '=', 0),
                 ('reconciled', '=', False)])

    @api.multi
    def action_view_receivable_payable(self):
        if self.partner_type == 'supplier':
            action_ref = 'br_account_payment.action_payable_move_lines'
        else:
            action_ref = 'br_account_payment.action_receivable_move_line'

        action = self.env.ref(action_ref).read()[0]
        action['context'] = {'search_default_partner_id': self.partner_id.id}

        return action
    '''
    def action_validate_invoice_payment(self):
        if self.payment_mode_id.payment_method == 'boleto':
            raise ValidationError(_("Pagamentos realizados através de Boleto Bancário só podem ser liquidados através "
                                    "de documento eletrônico. Escolha outro método de Pagamento ou faça a importação"
                                    "do arquivo de retorno do seu Banco."))
        res = super(AccountPayment, self).action_validate_invoice_payment()

        return res
    '''