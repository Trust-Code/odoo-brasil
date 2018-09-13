# -*- coding: utf-8 -*-
# © 2017 Danimar Ribeiro <danimaribeiro@gmail.com>, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from datetime import datetime
from odoo import api, fields, models


class AccountClose(models.TransientModel):
    _name = 'account.close.wizard'

    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")
    partner_id = fields.Many2one(
        string="Parceiro",
        comodel_name="res.partner",
        help="Parceiro para o qual serão geradas as contas a pagar.",
    )
    payment_date = fields.Date(
        string="Data do vencimento",
        help="Data do vencimento das contas a pagar geradas.",
    )
    account_id = fields.Many2one(
        string="Conta",
        comodel_name="account.account",
        help="Conta de lançamento dos impostos.",
    )
    journal_id = fields.Many2one(
        string="Diário",
        comodel_name="account.journal",
        help="Diário no qual a conta será lançada.",
    )
    account_payment_id = fields.Many2one(
        string="Conta de pagamento dos impostos.",
        comodel_name="account.account",
        help="Conta para pagamento dos impostos lançados.",
    )

    @api.multi
    def action_close_period(self):

        self.env.cr.execute(
            "select sum(debit+credit), account_id from account_move_line \
            where account_id in (select account_account_id from \
            account_account_l10n_br_taxation_simples_rel) \
            and date >= date_trunc('month',current_date - interval '13' month)\
            and date < date_trunc('month',current_date - interval '1' month)\
            group by account_id;")

        total_revenue = self.env.cr.fetchall()[0][0]
        self.env.cr.execute(
            "select sum(debit+credit), account_id from account_move_line \
            where account_id in (select account_account_id from \
            account_account_l10n_br_taxation_simples_rel) \
            and date >= date_trunc('month', current_date - interval '1' month)\
            and date < date_trunc('month', current_date)\
            group by account_id;")

        data = self.env.cr.fetchall()
        taxes = self.env['l10n_br.taxation.simples'].search([])
        for tax in taxes:
            acc_ids = tax.account_ids.ids

            revenue = sum([x[0] for x in data if x[1] in acc_ids])
            if tax.start_revenue < total_revenue < tax.end_revenue:

                fee = total_revenue * (tax.amount_tax / 100)
                fee = (fee - tax.amount_deduction) / total_revenue

                self.create_account_vouchers_simples_nacional(fee * revenue)

    def prepare_account_voucher(self):
        vals = dict(
            partner_id=self.partner_id.id,
            pay_now='pay_later',
            date=datetime.strftime(datetime.now(), '%Y-%m-%d'),
            date_due=self.payment_date,
            account_date=self.payment_date,
            account_id=self.account_id.id,
            journal_id=self.journal_id.id,
            voucher_type='purchase',
            line_ids=[],
        )
        return vals

    def prepare_account_line_voucher(self, domain, price_unit):
        vals = dict(
            name=domain,
            account_id=self.account_payment_id.id,
            quantity=1,
            price_unit=price_unit,
        )
        return [0, 0, vals]

    def create_account_vouchers_simples_nacional(self, price):
        account_voucher = self.prepare_account_voucher()
        voucher_line = [self.prepare_account_line_voucher(
            'Simples Nacional', price)]
        account_voucher['line_ids'] = voucher_line
        self.env['account.voucher'].create(account_voucher)
