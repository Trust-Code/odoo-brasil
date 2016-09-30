# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import api, fields, models


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    @api.multi
    @api.depends('debit', 'credit', 'user_type_id', 'amount_residual')
    def _compute_payment_value(self):
        for item in self:
            item.payment_value = item.debit \
                if item.user_type_id.type == 'receivable' else item.credit * -1
    payment_value = fields.Float(
        string="Valor", compute=_compute_payment_value)
