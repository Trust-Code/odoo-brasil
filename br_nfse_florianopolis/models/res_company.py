# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    aedf = fields.Char(string="Número AEDF", size=10,
                       help="Número de autorização para emissão de NFSe")
    client_id = fields.Char(string='Client Id', size=50)
    client_secret = fields.Char(string='Client Secret', size=50)
    user_password = fields.Char(string='Senha Acesso', size=50)
