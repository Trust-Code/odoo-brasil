# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class AccountAccountTemplate(models.Model):
    _inherit = 'account.account.template'

    account_type = fields.Selection(
        [('tax', 'Tax'), ('income', 'Income'), ('expense', 'Expense')],
        string="Account Type")


class AccountAccount(models.Model):
    _inherit = 'account.account'

    account_type = fields.Selection(
        [('tax', 'Tax'), ('income', 'Income'), ('expense', 'Expense')],
        string="Account Type")


class AccountPaymentTerm(models.Model):
    _inherit = 'account.payment.term'

    indPag = fields.Selection(
        [('0', u'Cash Payment'), ('1', u'Deferred Payment'),
         ('2', 'Other')], 'Payment Indicator', default='1')
