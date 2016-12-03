# -*- coding: utf-8 -*-
# © 2009  Renato Lima - Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import models, fields


class ResCountry(models.Model):
    _inherit = 'res.country'

    bc_code = fields.Char(u'Código BC', size=5)
    ibge_code = fields.Char(u'Código IBGE', size=5)
    siscomex_code = fields.Char(u'Código Siscomex', size=4)


class ResCountryState(models.Model):
    _inherit = 'res.country.state'

    ibge_code = fields.Char(u'Código IBGE', size=2)
