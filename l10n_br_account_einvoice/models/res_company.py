# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    nfe_a1_file = fields.Binary('Arquivo NFe A1')
    nfe_a1_password = fields.Char('Senha NFe A1', size=64)
