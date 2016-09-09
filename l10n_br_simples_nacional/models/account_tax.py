# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import api, fields, models


class AccountTax(models.Model):
    _inherit = 'account.tax'

    domain = fields.Selection(selection_add=[('simples', 'Simples Nacional')])
    percent_credit = fields.Float(string="% Crédito ICMS")
