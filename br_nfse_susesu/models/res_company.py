# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    # Nota Susesu
    senha_ambiente_nfse = fields.Char(
        string=u'Senha NFSe', size=30, help=u'Senha Nota Fiscal de Serviço')
