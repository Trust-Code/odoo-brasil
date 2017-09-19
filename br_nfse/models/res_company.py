# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    tipo_ambiente_nfse = fields.Selection(
        [('1', u'Produção'), ('2', u'Homologação')],
        string="Ambiente NFSe", default='2')

    senha_ambiente_nfse = fields.Char(
        string=u'Senha NFSe', size=30, help=u'Senha Nota Fiscal de Serviço')

    codigo_nfse_empresa = fields.Char(string="Cód. NFSe - Imperial", size=70)
    codigo_nfse_usuario = fields.Char(
        string="Usuário NFSe - Imperial", size=70)
