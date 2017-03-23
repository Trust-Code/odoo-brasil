# -*- coding: utf-8 -*-
# © 2015 Danimar Ribeiro <danimaribeiro@gmail.com>, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import models, fields


class ResCompany(models.Model):
    _inherit = 'res.company'

    last_nsu_nfe = fields.Char(string="Último NSU usado", size=20, default='0')
