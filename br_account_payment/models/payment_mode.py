# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class PaymentMode(models.Model):
    _name = "payment.mode"
    _description = 'Modo de Pagamento'
    _order = 'name'

    name = fields.Char(string='Name', required=True, translate=True)
    type = fields.Selection(
        [('receivable', 'Recebível'), ('payable', 'Pagável')],
        string="Tipo de Transação", default='receivable')
    company_id = fields.Many2one(
        'res.company', string='Company', required=True, ondelete='restrict',
        default=lambda self: self.env['res.company']._company_default_get(
            'account.payment.mode'))
    active = fields.Boolean(string='Active', default=True)
    bank_account_id = fields.Many2one(
        'res.partner.bank', string="Bank Account", ondelete='restrict')
