# -*- coding: utf-8 -*-
# © 2016 Alessandro Fernandes Martini, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    move_line_id = fields.Many2one('account.move.line',
                                   string="Linha de fatura")

    @api.model
    def default_get(self, fields):
        rec = super(AccountPayment, self).default_get(fields)
        if self.env.context.get('default_move_line_id', False):
            rec['amount'] = self.env.context.get('default_amount',
                                                 rec['amount'])
        return rec

    def _create_payment_entry(self, amount):
        self = self.with_context(move_line_to_reconcile=self.move_line_id)
        return super(AccountPayment, self)._create_payment_entry(amount)
