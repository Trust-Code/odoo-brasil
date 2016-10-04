# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import fields, models


class AccountTaxTemplate(models.Model):
    _inherit = 'account.tax.template'

    deduced_account_id = fields.Many2one(
        'account.account', string="Conta de Dedução da Venda")
    refund_deduced_account_id = fields.Many2one(
        'account.account', string="Conta de Dedução do Reembolso")
    cst = fields.Char(string="CST", size=4)
    domain = fields.Selection([('icms', 'ICMS'),
                               ('pis', 'PIS'),
                               ('cofins', 'COFINS'),
                               ('ipi', 'IPI'),
                               ('issqn', 'ISSQN'),
                               ('ii', 'II'),
                               ('outros', 'Outros')], string="Tipo")


class AccountTax(models.Model):
    _inherit = 'account.tax'

    deduced_account_id = fields.Many2one(
        'account.account', string="Conta de Dedução da Venda")
    refund_deduced_account_id = fields.Many2one(
        'account.account', string="Conta de Dedução do Reembolso")
    cst = fields.Char(string="CST", size=4)
    domain = fields.Selection([('icms', 'ICMS'),
                               ('pis', 'PIS'),
                               ('cofins', 'COFINS'),
                               ('ipi', 'IPI'),
                               ('issqn', 'ISSQN'),
                               ('ii', 'II'),
                               ('outros', 'Outros')], string="Tipo")
