# -*- coding: utf-8 -*-
# © 2017 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import fields, models


class BrAccountCnae(models.Model):
    _inherit = 'br_account.cnae'

    id_cnae = fields.Char(string="Id CNAE", size=10)
