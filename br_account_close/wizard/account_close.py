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
        import ipdb
        ipdb.set_trace()
        account_move_lines=self.env['account.move.line'].search([
            ('date', '>=', self.start_date), ('date', '<=', self.end_date),
            ('account_id.account_type', '=', 'tax')])

        # icms_line = account_move_lines.filtered(
        #     lambda x: x.tax_line_id.domain == 'icms')
        domains=[]
        for lines in account_move_lines:
            domains.append(lines.tax_line_id.domain)

        domains=set(domains)

        for domain in domains:
            self.create_account_payment_tax(domain)

    def create_account_payment_tax(self, domain):
        vals=dict(
            partner_id = self.partner_id.id,
            pay_now = 'pay_later',
            date = datetime.now(),
            date_due = self.payment_date,
            account_date = self.payment_date,
            account_id = self.account_id.id,
            journal_id = self.journal_id.id,
        )
