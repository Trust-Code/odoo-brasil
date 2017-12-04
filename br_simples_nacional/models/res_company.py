# -*- coding: utf-8 -*-
# © 2017 Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields


class ResCompany(models.Model):
    _inherit = 'res.company'

    simples_nacional_ids = fields.One2many('simples.nacional', 'company_id',
                                           string='Simples Nacional')
