# -*- coding: utf-8 -*-
# © 2016 Alessandro Fernandes Martini, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    acc_number_dig = fields.Char(related='bank_account_id.acc_number_dig')
    bank_agency_number = fields.Char(related='bank_account_id.bra_number')
    bank_agency_dig = fields.Char(related='bank_account_id.bra_number_dig')
    acc_partner_id = fields.Many2one('res.partner',
                                     related='bank_account_id.partner_id')
    bank_currency_id = fields.Many2one('res.currency', string="Bank Account",
                                       related='bank_account_id.currency_id')

    def set_bank_account(self, acc_number, bank_id=None):
        self.ensure_one()
        vals = {
            'acc_number': acc_number,
            'acc_number_dig': self.acc_number_dig,
            'bra_number': self.bank_agency_number,
            'bra_number_dig': self.bank_agency_dig,
            'bank_id': bank_id,
            'company_id': self.company_id.id,
            'currency_id': self.currency_id.id,
            'partner_id': self.company_id.partner_id.id,
        }
        super(AccountJournal, self).set_bank_account(acc_number, bank_id)
        self.bank_account_id.write(vals)
