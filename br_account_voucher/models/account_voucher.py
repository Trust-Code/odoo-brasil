# -*- coding: utf-8 -*-
# © 2018 Johny Chen Jy <johnychenjy@gmail.com>, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, api


class AccountVoucher(models.Model):
    _inherit = 'account.voucher'

    @api.multi
    def voucher_move_line_create(self, line_total, move_id, company_currency,
                                 current_currency):
        line_total = super(AccountVoucher, self).voucher_move_line_create(
            line_total, move_id, company_currency, current_currency)
        move = self.env['account.move'].browse(move_id)
        for line in move.line_ids:
            line2 = self.line_ids.filtered(
                lambda x: x.account_id.id == line.account_id.id and
                (x.price_subtotal if current_currency != company_currency else
                 0.0) == line.amount_currency)
            line.analytic_tag_ids = [(6, False, line2.analytic_tag_ids.ids)]

        return line_total
