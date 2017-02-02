# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# © 2017 Carlos Alberto Cipriano Korovsky, UKTech
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models

class AccountJournal(models.Model):
    _inherit = 'account.journal'

    bank_acc_number = fields.Char(related='bank_account_id.brl_acc_number')
    
    bank_ofx_acc_number = fields.Char(related='bank_account_id.acc_number')
    
    bank_acc_number_dig = fields.Char(oldname='acc_number_dig', 
        related='bank_account_id.brl_acc_number_digit')
    bank_agency_number = fields.Char(related='bank_account_id.brl_bra_number')
    bank_agency_dig = fields.Char(related='bank_account_id.brl_bra_number_digit')
    acc_partner_id = fields.Many2one('res.partner',
                                     related='bank_account_id.partner_id')
    bank_currency_id = fields.Many2one('res.currency', string="Bank Account",
                                       related='bank_account_id.currency_id')

    @api.multi
    def write(self, vals):
        result = super(AccountJournal, self).write(vals)
        # Create the bank_account_id if necessary
        if 'bank_acc_number' in vals:
            for journal in self.filtered(lambda r: r.type == 'bank' and not r.bank_account_id):
                journal.set_brl_bank_account(vals.get('bank_acc_number'), 
                    vals.get('bank_acc_number_dig'), 
                    vals.get('bank_agency_number'), vals.get('bank_agency_dig'),
                    vals.get('bank_id'))

        return result
    
    @api.model
    def create(self, vals):
        journal = super(AccountJournal, self).create(vals)
        # Create the bank_account_id if necessary
        if ((journal.type == 'bank') and (not journal.bank_account_id) and (vals.get('bank_acc_number'))):
            journal.set_brl_bank_account(vals.get('bank_acc_number'), 
                vals.get('bank_acc_number_dig'), vals.get('bank_agency_number'), 
                vals.get('bank_agency_dig'), vals.get('bank_id'))
        return journal
    
    def set_bank_account(self, acc_number, bank_id=None):
        """ Disabled to create an Brazilian Bank Account """
        return
    
    def set_brl_bank_account(self, brl_acc_number, brl_acc_number_digit=None,
        brl_bra_number=None, brl_bra_number_digit=None, bank_id=None):
        """ Create a res.partner.bank and set it as value of the field bank_account_id """
        self.ensure_one()
        self.bank_account_id = self.env['res.partner.bank'].create({
            'brl_bra_number': brl_bra_number or '',
            'brl_bra_number_digit': brl_bra_number_digit or '',
            'brl_acc_number': brl_acc_number,
            'brl_acc_number_digit': brl_acc_number_digit or '',
            'bank_id': bank_id,
            'company_id': self.company_id.id,
            'currency_id': self.currency_id.id,
            'partner_id': self.company_id.partner_id.id,
        }).id
        

class AccountPaymentTerm(models.Model):
    _inherit = 'account.payment.term'

    indPag = fields.Selection(
        [('0', u'Pagamento à Vista'), ('1', u'Pagamento à Prazo'),
         ('2', 'Outros')], 'Indicador de Pagamento', default='1')
