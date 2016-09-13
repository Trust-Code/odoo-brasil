# -*- coding: utf-8 -*-
# © 2014 KMEE (http://www.kmee.com.br)
# @author  Rafael da Silva Lima <rafael.lima@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    check_benefits = fields.Boolean(
        'Valley Food and Meal Valley simultaneous', required=False)
