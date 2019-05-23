# © 2019 Mackilem Van der Laan, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models
from odoo.tools.safe_eval import safe_eval


class AccountTax(models.Model):
    _inherit = 'account.tax'

    def _compute_amount(self, base_amount, price_unit, quantity=1.0,
                        product=None, partner=None):
        self.ensure_one()
        if self.amount_type == 'code':
            company = self.env.user.company_id
            invoice_amount = self._context.get('invoice_amount', 0)
            localdict = {
                'invoice_amount': invoice_amount,
                'base_amount': base_amount,
                'price_unit': price_unit,
                'quantity': quantity,
                'product': product,
                'partner': partner,
                'company': company,
                'context': self._context,
            }
            safe_eval(self.python_compute, localdict, mode="exec", nocopy=True)
            return localdict['result']
        return super(AccountTax, self)._compute_amount(
            base_amount, price_unit, quantity, product, partner)
