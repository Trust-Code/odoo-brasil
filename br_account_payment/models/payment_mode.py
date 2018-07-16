# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models, api

# Métodos de Pagamento conforme modelo para emissão de NF-e
metodos = [
    ('01', u'01 - Dinheiro'),
    ('02', u'02 - Cheque'),
    ('03', u'03 - Cartão de Crédito'),
    ('04', u'04 - Cartão de Débito'),
    ('05', u'05 - Crédito Loja'),
    ('10', u'10 - Vale Alimentacão'),
    ('11', u'11 - Vale Refeição'),
    ('12', u'12 - Vale Presente'),
    ('13', u'13 - Vale Combustível'),
    ('15', u'15 - Boleto Bancário'),
    ('90', u'90 - Sem Pagamento'),
    ('99', u'99 - Outros'), ]

class PaymentMode(models.Model):
    _name = "payment.mode"
    _description = 'Payment Modes'
    _order = 'name'

    name = fields.Char(string='Name', required=True, translate=True)
    company_id = fields.Many2one('res.company', string='Company', required=True, ondelete='restrict',
                                 default=lambda self: self.env['res.company']._company_default_get('account.payment.mode'))
    active = fields.Boolean(string='Active', default=True)
    bank_account_id = fields.Many2one('res.partner.bank', string="Bank Account", ondelete='restrict')
    payment_method = fields.Selection(metodos, string='Método de Pagamento')
    journal_id = fields.Many2one('account.journal', string='Diário', domain=[('type', 'in', ['cash', 'bank'])])

    @api.onchange('bank_account_id')
    def _compute_bank_journal(self):
        self.ensure_one()
        self.journal_id = self.bank_account_id.journal_id