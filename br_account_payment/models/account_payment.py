# -*- coding: utf-8 -*-
# © 2016 Alessandro Fernandes Martini, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models, _


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
        if self.invoice_ids:
            return super(AccountPayment, self)._create_payment_entry(amount)

        aml_obj = self.env['account.move.line'].with_context(
            check_move_validity=False)
        counterpart_debit, counterpart_credit, amount_currency, currency_id =\
            aml_obj.with_context(date=self.payment_date).compute_amount_fields(
                amount, self.currency_id, self.company_id.currency_id)

        move = self.env['account.move'].create(self._get_move_vals())

        counterpart_aml_dict = self._get_shared_move_line_vals(
            counterpart_debit, counterpart_credit, amount_currency, move.id)
        counterpart_aml_dict.update(self._get_counterpart_move_line_vals(
            self.invoice_ids))
        counterpart_aml_dict.update({'currency_id': currency_id})
        counterpart_aml = aml_obj.create(counterpart_aml_dict)

        if self.payment_difference_handling == 'reconcile'\
                and self.payment_difference:
            writeoff_line = self._get_shared_move_line_vals(
                0, 0, 0, move.id)
            amount_currency_wo, currency_id = aml_obj.with_context(
                date=self.payment_date).compute_amount_fields(
                    self.payment_difference, self.currency_id,
                    self.company_id.currency_id)[2:]

            if  counterpart_debit > 0:
                debit_wo = abs(self.payment_difference)
                credit_wo = 0.0
                amount_currency_wo = abs(amount_currency_wo)
            else:
                debit_wo = 0.0
                credit_wo = abs(self.payment_difference)
                amount_currency_wo = -abs(amount_currency_wo)

            writeoff_line.update({
                'name': _('Counterpart'),
                'account_id': self.writeoff_account_id.id,
                'debit': debit_wo,
                'credit': credit_wo,
                'amount_currency': amount_currency_wo,
                'currency_id': currency_id
            })

            writeoff_line = aml_obj.create(writeoff_line)

            if counterpart_aml['debit']:
                counterpart_aml['debit'] += credit_wo - debit_wo
            if counterpart_aml['credit']:
                counterpart_aml['credit'] += debit_wo - credit_wo
            counterpart_aml['amount_currency'] -= amount_currency_wo

        if not self.currency_id != self.company_id.currency_id:
            amount_currency = 0
        liquidity_aml_dict = self._get_shared_move_line_vals(
            counterpart_credit, counterpart_debit, -amount_currency, move.id)
        liquidity_aml_dict.update(self._get_liquidity_move_line_vals(-amount))
        aml_obj.create(liquidity_aml_dict)

        move.post()
        return move


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

    def _compute_payment_difference(self):
        super(AccountPayment, self)._compute_payment_difference()
        if len(self.invoice_ids) == 0:
            move_line = self.env['account.move.line'].browse(
                self.env.context.get('active_id'))
            diff = (move_line.debit or move_line.credit) - self.amount
            self.payment_difference = diff if diff < 0 else 0
