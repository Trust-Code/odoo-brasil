# -*- coding: utf-8 -*-
# © 2016 Alessandro Fernandes Martini, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    tipo_ambiente = fields.Selection([('1', 'Produção'), ('2', 'Homologação')],
                                     string="Homologação", default=2)
