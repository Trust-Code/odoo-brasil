# -*- coding: utf-8 -*-
# © 2016 Alessandro Fernandes Martini, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class PaymentType(models.Model):
    _name = 'payment.type'

    name = fields.Char(max_length=30, string="Nome")
    code = fields.Char(max_length=30, string="Código")
