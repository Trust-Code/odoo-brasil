# -*- coding: utf-8 -*-
# © 2018 Johny Chen Jy, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    service_cnae = fields.Many2one(
        'br_account.cnae', string="CNAE do Serviço")
