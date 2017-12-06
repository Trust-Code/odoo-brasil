# -*- coding: utf-8 -*-
# © 2017 Danimar Ribeiro <danimaribeiro@gmail.com>, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import api, fields, models
from datetime import datetime


class AccountClose(models.TransientModel):
    _name = 'account.close.wizard'

    start_date = fields.Date(string="Inicio")
    end_date = fields.Date(string="Final")
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
        taxes = self.env.user.company_id.taxes_ids
        account_ids = [line.account_id for line in taxes]
        account_move_lines = self.env['account.move.line'].search([
            ('date', '>=', self.start_date), ('date', '<=', self.end_date),
            ('account_id', 'in', account_ids)])

        domains = []
        for lines in account_move_lines:
            domains.append(lines.tax_line_id.domain)

        domains = set(domains)

        account_voucher = self.prepare_account_voucher()
        lines_ids = []
        if self.env.user.company_id.fiscal_type == '3':
            for domain in domains:
                price_unit = self.tax_calculation(account_move_lines, domain)
                lines_ids.append(self.prepare_account_line_voucher(
                    domain, price_unit))

            account_voucher['line_ids'] = lines_ids
            self.env['account.voucher'].create(account_voucher)
        else:
            prices_unit = self.tax_calculation_simples_nacional(
                account_move_lines)  # implementar filtros no wizard
            self.create_account_vouchers_simples_nacional(prices_unit)

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

    def create_account_vouchers_simples_nacional(self, prices):
        for line in prices.keys():
            account_voucher = self.prepare_account_voucher()
            voucher_line = [self.prepare_account_line_voucher(
                'Simples Nacional', prices[line])]
            account_voucher['line_ids'] = voucher_line
            self.env['account.voucher'].create(account_voucher)

    def tax_calculation(self, account_move_lines, domain=False):
        tax_lines = account_move_lines
        if domain:
            tax_lines = account_move_lines.filtered(
                lambda x: x.tax_line_id.domain == domain)

        tax_credit = 0
        tax_debit = 0

        for lines in tax_lines:
            tax_credit += lines.credit
            tax_debit += lines.debit

        return tax_credit - tax_debit

    def tax_calculation_simples_nacional(self, account_move_lines):
        taxes = self.env.company_id.compute_new_aliquot_simples_nacional()
        taxes_amount = {}
        for line in taxes.keys():
            tax_lines = account_move_lines.filtered(
                lambda x: x.account_id == line.account_id
            )
            amount = self.tax_calculation(tax_lines)
            tax_amount = amount*taxes[line]
            taxes_amount.update({line: tax_amount})
        return taxes_amount
