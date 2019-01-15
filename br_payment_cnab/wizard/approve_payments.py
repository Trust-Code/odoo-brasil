# © 2018 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import fields, models


class l10nBrPaymentApprove(models.TransientModel):
    _name = 'l10n_br_payment.approve'

    name = fields.Char(string="Nome")

    def action_approve_payments(self):
        context = dict(self._context or {})
        active_ids = context.get('active_ids', []) or []
        line_ids = self.env['payment.order.line'].browse(active_ids)

        line_ids.action_aprove_payment_line()
