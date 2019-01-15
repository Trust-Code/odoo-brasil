# -*- coding: utf-8 -*-
# © 2016 Alessandro Fernandes Martini, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    l10n_br_sequence_statements = fields.Many2one(
        'ir.sequence', string="Sequência Extratos de Retorno")

    acc_number_dig = fields.Char(related='bank_account_id.acc_number_dig')
    bank_agency_number = fields.Char(related='bank_account_id.bra_number')
    bank_agency_dig = fields.Char(related='bank_account_id.bra_number_dig')
    acc_partner_id = fields.Many2one('res.partner',
                                     related='bank_account_id.partner_id')

    @api.multi
    def write(self, vals):
        result = super(AccountJournal, self).write(vals)
        journal_ids = self.filtered(
            lambda r: r.type == 'bank' and r.bank_account_id)
        for journal in journal_ids:
            acc_vals = {
                'acc_number_dig': vals.get('acc_number_dig'),
                'bra_number': vals.get('bank_agency_number'),
                'bra_number_dig': vals.get('bank_agency_dig'),
                'currency_id': vals.get('currency_id'),
                'partner_id': vals.get('acc_partner_id'),
            }
            acc_vals = {k: v for k, v in acc_vals.items() if v}
            journal.bank_account_id.write(acc_vals)
        return result

    @api.model
    def create(self, vals):
        journal = super(AccountJournal, self).create(vals)
        if journal.bank_account_id:
            acc_vals = {
                'acc_number_dig': vals.get('acc_number_dig'),
                'bra_number': vals.get('bank_agency_number'),
                'bra_number_dig': vals.get('bank_agency_dig'),
                'currency_id': vals.get('currency_id'),
                'partner_id': vals.get('acc_partner_id'),
            }
            acc_vals = {k: v for k, v in acc_vals.items() if v}
            journal.bank_account_id.write(acc_vals)
        return journal
