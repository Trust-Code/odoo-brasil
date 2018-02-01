# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro <danimaribeiro@gmail.com>, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class BrAccountServiceType(models.Model):
    _inherit = 'br_account.service.type'

    codigo_servico_paulistana = fields.Char(
        string=u'Código NFSe Paulistana', size=5)

    codigo_tributacao_municipio = fields.Char(
        string=u"Cód. Tribut. Munic.", size=20,
        help="Código de Tributação no Munípio")
