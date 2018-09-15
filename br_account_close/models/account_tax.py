# © 2018 Danimar Ribeiro <danimaribeiro@gmail.com>, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import fields, models


class AccountTaxTemplate(models.Model):
    _inherit = 'account.tax.template'

    domain = fields.Selection(selection_add=[('simples', 'Simples Nacional')])


class AccountTax(models.Model):
    _inherit = 'account.tax'

    domain = fields.Selection(selection_add=[('simples', 'Simples Nacional')])
    l10n_br_tax_interval_ids = fields.One2many(
        'l10n_br.taxation.simples', 'tax_id', string="Tax Rules")
    l10n_br_revenue_account_ids = fields.Many2many(
        'account.account', string="Revenue Accounts")

    def aggregate_tax_to_pay(self, period):
        if self.domain == 'simples':
            return self._calculate_simples_nacional_tax()
        return self._calulate_amount_tax_period(period)

    def _calulate_amount_tax_period(self, period):
        if not self.account_id:
            return 0
        acc_ids = [self.account_id.id]
        if self.account_id.l10n_br_credit_account_id:
            acc_ids += [self.account_id.l10n_br_credit_account_id.id]
        self.env.cr.execute(
            "select sum(credit-debit) from account_move_line \
            where account_id in %s \
            and date >= date_trunc('month', current_date - interval %s month)\
            and date < date_trunc('month', current_date)",
            (tuple(acc_ids), str(period)))
        result = self.env.cr.fetchall()
        return result and result[0] and result[0][0] or 0.0

    # Necessary because is not a matter of sum the taxes over the month
    def _calculate_simples_nacional_tax(self):
        acc_ids = self.l10n_br_revenue_account_ids.ids
        self.env.cr.execute(
            "select sum(debit+credit), account_id from account_move_line \
            where account_id in %s \
            and date >= date_trunc('month',current_date - interval '13' month)\
            and date < date_trunc('month',current_date - interval '1' month)\
            group by account_id;", (tuple(acc_ids),))

        result = self.env.cr.fetchall()
        total_revenue = result and result[0] and result[0][0] or 0.0
        if total_revenue <= 0:
            return 0.0
        self.env.cr.execute(
            "select sum(debit+credit), account_id from account_move_line \
            where account_id in %s \
            and date >= date_trunc('month', current_date - interval '1' month)\
            and date < date_trunc('month', current_date)\
            group by account_id;", (tuple(acc_ids),))

        data = self.env.cr.fetchall()
        for tax in self.l10n_br_tax_interval_ids:
            revenue = sum([x[0] for x in data if x[1] in acc_ids])
            if tax.start_revenue <= total_revenue < tax.end_revenue:
                # Cálculo do simples Nacional
                fee = total_revenue * (tax.amount_tax / 100)
                fee = (fee - tax.amount_deduction) / total_revenue

                return fee * revenue
        return 0.0
