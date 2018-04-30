# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models, api


class PaymentMode(models.Model):
    _name = "payment.mode"
    _description = 'Payment Modes'
    _order = 'name'

    name = fields.Char(string='Name', required=True, translate=True)
    company_id = fields.Many2one('res.company', string='Company', required=True, ondelete='restrict',
                    default=lambda self: self.env['res.company']._company_default_get('account.payment.mode'))
    active = fields.Boolean(string='Active', default=True)
    bank_account_id = fields.Many2one(
        'res.partner.bank', string="Bank Account", ondelete='restrict')
    payment_method = fields.Selection([('dinheiro', u'Dinheiro'),('cheque', u'Cheque'),
                                       ('deposito',u'Depósito em Conta'),('outro', u'Outro'),],
                                      string='Método de Pagamento')
    journal_id = fields.Many2one('account.journal', string='Diário',
                                 domain=[('type','in',['cash','bank'])])

    @api.onchange('bank_account_id')
    def _compute_bank_journal(self):
        self.journal_id = self.bank_account_id.journal_id
