# -*- coding: utf-8 -*-
# © 2017 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, models


class BoletoSendEmail(models.TransientModel):
    _name = 'boleto.send.email'

    @api.multi
    def send_boletos_by_email(self):
        context = dict(self._context or {})
        active_ids = context.get('active_ids', []) or []
        invoices = self.env['account.invoice'].browse(active_ids)
        invoices.send_email_boleto_queue()
        return {'type': 'ir.actions.act_window_close'}
