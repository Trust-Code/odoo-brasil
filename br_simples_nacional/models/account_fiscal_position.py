# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro <danimaribeiro@gmail.com>, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import api, fields, models



class AccountFiscalPositionTaxRule(models.Model):
    _inherit = 'account.fiscal.position.tax.rule'




class AccountFiscalPosition(models.Model):
    _inherit = 'account.fiscal.position'
