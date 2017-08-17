# -*- coding: utf-8 -*-
# © 2016 Alessandro Fernandes Martini, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    move_line_id = fields.Many2one('account.move.line',
                                   string="Linha de fatura")
    count_payments = fields.Integer('Linha(s)',
        compute = 'compute_count_payments')

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
    def compute_count_payments(self):
        if self.partner_type == 'supplier':
            account_type = 'payable'
        else:
            account_type = 'receivable'

        self.count_payments = self.env['account.move.line'].search_count(
            [('partner_id', '=', self.partner_id.id),
            ('user_type_id.type', '=', account_type),
            ('amount_residual', '!=', 0)])

    @api.multi
    def action_view_account_payment(self):
        if self.partner_type == 'supplier':
            action_ref = 'br_account_payment.action_payable_move_lines'
        else:
            action_ref = 'br_account_payment.action_receivable_move_line'

        action = self.env.ref(action_ref).read()[0]
        action['context'] = {'search_default_partner_id': self.partner_id.id}

        return action
