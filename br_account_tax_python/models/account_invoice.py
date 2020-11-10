# © 2019 Mackilem Van der Laan, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    def _prepare_tax_context(self):
        res = super(AccountInvoiceLine, self)._prepare_tax_context()
        lines = self.invoice_id.invoice_line_ids
        amount_total = sum((l.quantity * l.price_unit) +
                           l.l10n_br_price_tax - l.l10n_br_valor_desconto
                           for l in lines)
        amount = (amount_total
                  + self.quantity * self.price_unit)
        res['invoice_amount'] = amount
        return res
