# © 2018 Johny Chen Jy <johnychenjy@gmail.com>, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from datetime import date
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models
from odoo.tools import float_is_zero


class AccountVoucher(models.Model):
    _inherit = 'account.voucher'

    l10n_br_recurring = fields.Boolean(string="Recurring ?")
    l10n_br_post_automatic = fields.Boolean(string="Lançar automaticamente?")
    l10n_br_residual = fields.Monetary(
        string='Saldo', compute='_compute_residual',
        store=True, help="Saldo restante.")
    l10n_br_paid = fields.Boolean(string="Pago?", compute='_compute_residual')

    @api.one
    @api.depends('move_id.line_ids.amount_residual')
    def _compute_residual(self):
        residual = 0.0
        for line in self.sudo().move_id.line_ids:
            if line.account_id == self.account_id:
                residual += line.amount_residual
        precision = self.currency_id.rounding
        if float_is_zero(residual, precision_rounding=precision) \
           and self.state == 'posted':
            self.update({'l10n_br_residual': abs(residual),
                         'l10n_br_paid': True})
        else:
            self.update({'l10n_br_residual': abs(residual),
                         'l10n_br_paid': False})

    @api.multi
    def action_mark_done(self):
        self.write({'state': 'posted'})

    @api.multi
    def action_cancel_voucher(self):
        self.write({'state': 'cancel'})

    def calculate_amount_voucher_line(self, line):
        return line.price_unit

    def prepare_voucher_values_to_copy(self, vals):
        return vals

    def it_should_generate(self):
        current_date = fields.Date.from_string(self.date)
        due_date = fields.Date.from_string(self.date_due)
        if not due_date or not current_date:
            return False
        if current_date > date.today():
            return False
        if not self.line_ids:
            return False
        return True

    def generate_recurring_vouchers(self):
        vouchers = self.search(
            [('l10n_br_recurring', '=', True),
             ('state', '=', 'posted')])
        for item in vouchers:
            if not item.it_should_generate():
                continue
            current_date = fields.Date.from_string(item.date)
            due_date = fields.Date.from_string(item.date_due)
            vals = item.prepare_voucher_values_to_copy({
                'account_date': current_date,
                'date': current_date,
                'date_due': due_date,
                'l10n_br_recurring': False,
                'reference': item.reference,
            })
            voucher = item.copy(vals)
            for line in voucher.line_ids:
                amount = self.calculate_amount_voucher_line(line)
                line.price_unit = amount
            item.date = current_date + relativedelta(months=1)
            item.date_due = due_date + relativedelta(months=1)
            try:
                if item.l10n_br_post_automatic:
                    voucher.proforma_voucher()
            except:
                pass

    @api.multi
    def voucher_move_line_create(self, line_total, move_id, company_currency,
                                 current_currency):
        line_total = super(AccountVoucher, self).voucher_move_line_create(
            line_total, move_id, company_currency, current_currency)
        move = self.env['account.move'].browse(move_id)
        for line in move.line_ids:
            line2 = self.line_ids.filtered(
                lambda x: x.account_id.id == line.account_id.id and
                x.price_subtotal == line.balance)
            if len(line2) == 1:
                line.analytic_tag_ids = [(6, False, line2.analytic_tag_ids.ids)]

        return line_total

    @api.multi
    def first_move_line_get(self, move_id, company_currency, current_currency):
        vals = super(AccountVoucher, self).first_move_line_get(
            move_id, company_currency, current_currency)
        # Correção do valor quando retenção - tax_amount é negativo
        if self.tax_amount < 0.0:
            vals['credit'] += self.tax_amount
        return vals
