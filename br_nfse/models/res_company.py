# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    tipo_ambiente_nfse = fields.Selection(
        [('1', u'Produção'), ('2', u'Homologação')],
        string="Ambiente NFSe", default='2')

    # Nota Susesu
    senha_ambiente_nfse = fields.Char(
        string=u'Senha NFSe', size=30, help=u'Senha Nota Fiscal de Serviço')

    # Nota Imperial
    codigo_nfse_empresa = fields.Char(string="Cód. NFSe - Imperial", size=70)
    codigo_nfse_usuario = fields.Char(
        string="Usuário NFSe - Imperial", size=70)
    tipo_tributacao_imperial = fields.Selection(
        [('1', '1 - Tributado'),
         ('2', '2 - Isenção Imunidade'),
         ('3', '3 - Suspensão'),
         ('4', '4 - Simples Nacional'),
         ('5', '5 - ISS Fixo'),
         ('6', '6 - Tributado')], string="Tipo Tributação",
        help="Tipo de Tributação Prestador - Nota Imperial")
    iss_simples_nacional = fields.Float(string="ISS Simples Nacional")
    adesao_simples_nacional = fields.Date(string="Adesão Simples Nacional")
