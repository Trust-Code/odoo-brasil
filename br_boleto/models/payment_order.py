# © 2018 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models


class PaymentOrderLine(models.Model):
    _inherit = 'payment.order.line'

    def action_print_boleto(self):
        return self.env.ref(
            'br_boleto.action_boleto_account_invoice').report_action(self)
