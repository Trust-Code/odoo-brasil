# -*- coding: utf-8 -*-
# Fábio Luna - NDS Sistemas

from odoo import fields, models


class MulticompanyPayment(models.TransientModel):
    _name = 'multicompany.payment.wizard'

    partner_id = fields.Many2one(
        string="Partner",
        comodel_name="res.partner",
    )

    def button_receivable_move_line_search(self):
        moves = self.env['multicompany.payment'].get_moves(self.partner_id)

        dummy, action_id = self.env['ir.model.data'].get_object_reference(
            'br_account_payment', 'multicompany_payment_action')
        vals = self.env['ir.actions.act_window'].browse(action_id).read()[0]
        vals['domain'] = [('id', 'in', moves.ids)]
        return vals
