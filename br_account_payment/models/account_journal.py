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
    bank_currency_id = fields.Many2one('res.currency',
                                       related='bank_account_id.currency_id')
