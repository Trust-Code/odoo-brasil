# © 2019 Mackilem, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class PaymentOrderLine(models.Model):
    _inherit = 'payment.order.line'

    expense_sheet_id = fields.Many2one('hr.expense.sheet', "Despesa de Origem")
