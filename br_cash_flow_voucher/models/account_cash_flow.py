# © 2018 Danimar Ribeiro <danimaribeiro@gmail.com>, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from datetime import date
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models


class AccountCashFlow(models.TransientModel):
    _inherit = 'account.cash.flow'

    @api.multi
    def calculate_moves(self):
        moves = super(AccountCashFlow, self).calculate_moves()

        new_moves = []
        vouchers = self.env['account.voucher'].search(
            [('l10n_br_recurring', '=', True),
             ('state', '=', 'posted'),
             ('date_due', '>=', date.today())])
        for voucher in vouchers:
            if not voucher.line_ids:
                continue

            due_date = fields.Date.from_string(voucher.date_due)
            max_date = fields.Date.from_string(self.end_date)
            while due_date <= max_date:
                new_moves.append({
                    'name': voucher.name or voucher.line_ids[0].name,
                    'cashflow_id': self.id,
                    'partner_id': voucher.partner_id.id,
                    'journal_id': voucher.journal_id.id,
                    'account_id': voucher.line_ids[0].account_id.id,
                    'line_type': voucher.account_id.internal_type,
                    'date': due_date.strftime('%Y-%m-%d'),
                    'debit': voucher.amount * -1
                    if voucher.voucher_type == 'purchase' else 0.0,
                    'credit': voucher.amount
                    if voucher.voucher_type == 'sale' else 0.0,
                    'amount': voucher.amount * -1
                    if voucher.voucher_type == 'purchase' else voucher.amount,
                })
                due_date = due_date + relativedelta(months=1)

        return moves + new_moves
