# -*- coding: utf-8 -*-
# © 2016 Alessandro Martini <alessandrofmartini@gmail.com>, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class InutilizedNfe(models.Model):
    _name = 'invoice.eletronic.inutilized'

    numero_inicial = fields.Integer('Numero Inicial')
    numero_final = fields.Integer('Numero Final')
