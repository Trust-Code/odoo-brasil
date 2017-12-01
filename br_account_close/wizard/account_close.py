# -*- coding: utf-8 -*-
# © 2017 Danimar Ribeiro <danimaribeiro@gmail.com>, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import api, fields, models


class AccountClose(models.TransientModel):
    _name = 'account.close.wizard'

    start_date = fields.Date(string="Inicio")
    end_date = fields.Date(string="Final")

    @api.multi
    def action_close_period(self):
        import ipdb
        ipdb.set_trace()
        account_move_lines = self.env['account.move.line'].search([
            ('date', '>=', self.start_date), ('date', '<=', self.end_date),
            ('account_id.account_type', '=', 'tax')])

        # icms_line = account_move_lines.filtered(
        #     lambda x: x.tax_line_id.domain == 'icms')
        domains = []
        for lines in account_move_lines:
            domains.append(lines.tax_line_id.domain)

        domains = set(domains)

        for domain in domains:
            self.create_account_payment_tax(domain)

    def create_account_payment_tax(self, domain):
        pass
