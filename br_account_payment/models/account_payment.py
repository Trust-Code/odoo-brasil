# -*- coding: utf-8 -*-
# © 2016 Alessandro Fernandes Martini, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    move_line_id = fields.Many2one('account.move.line',
                                   string="Linha de fatura")
    total_moves = fields.Integer(
        'Linha(s)', compute='_compute_open_moves')

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
