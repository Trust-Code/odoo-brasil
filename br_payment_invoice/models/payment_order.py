# © 2018 Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class PaymentOrderLine(models.Model):
    _inherit = 'payment.order.line'

    invoice_id = fields.Many2one(
        'account.invoice', string="Fatura Origem")
    partner_ref = fields.Char(string="Ref. Parceiro")
