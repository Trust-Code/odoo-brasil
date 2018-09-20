# © 2018 Danimar Ribeiro <danimaribeiro@gmail.com>, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from datetime import date
from calendar import monthrange
from odoo import fields, models, _
from dateutil.relativedelta import relativedelta


class AccountVoucher(models.Model):
    _inherit = 'account.voucher'

    l10n_br_tax_ids = fields.Many2many(
        'account.tax', string="Tax to compute",
        help="If selected compute the voucher value \
        according to the tax to pay",
        readonly=True, states={'draft': [('readonly', False)]})
    l10n_br_months_compute = fields.Integer(
        string="Period (months)", help="Period in months to compute",
        default=1, readonly=True, states={'draft': [('readonly', False)]})

    def prepare_voucher_values_to_copy(self, vals):
        vals = super(AccountVoucher, self).prepare_voucher_values_to_copy(vals)
        # Calculate first and last day of the period
        go_back = self.l10n_br_months_compute * -1
        last_month = date.today() + relativedelta(months=-1)
        last_day = monthrange(last_month.year, last_month.month)[1]
        last_month = last_month.replace(day=last_day)
        start_month = date.today() + relativedelta(months=go_back)
        start_month = start_month.replace(day=1)
        if self.l10n_br_tax_ids:
            name_taxes = ' '.join([x.name for x in self.l10n_br_tax_ids])
            description = _("%s - Period from %s to %s") % (
                name_taxes, start_month, last_month)
            vals.update({
                'narration': description,
                'account_date': last_month
            })
        return vals

    def calculate_amount_voucher_line(self, line):
        voucher = line.voucher_id
        if len(voucher.l10n_br_tax_ids) > 0:
            return voucher.l10n_br_tax_ids.aggregate_tax_to_pay(
                voucher.l10n_br_months_compute or 1)
        return super(AccountVoucher, self).calculate_amount_voucher_line(line)
