# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    tipo_ambiente_nfse = fields.Selection(
        [('1', u'Produção'), ('2', u'Homologação')],
        string="Ambiente NFSe", default='2')
