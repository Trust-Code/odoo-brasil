# -*- coding: utf-8 -*-
# © 2016 Alessandro Fernandes Martini, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class InvoiceEletronicItem(models.Model):
    _inherit = "invoice.eletronic.item"

    # ----------- ICMS INTERESTADUAL -----------
    has_icms_interestadual = fields.Boolean(u'Possui ICMS Interestadual')
    icms_bc_uf_dest = fields.Float(u'Valor da Base de Cálculo da UF de \
Destino')
    icms_aliquota_fcp_uf_dest = fields.Float(u'% Fundo de Combate à Pobreza \
na UF de Destino')
    icms_aliquota_uf_dest = fields.Float(u'% ICMS da UF de Destino')
    icms_aliquota_interestadual = fields.Float(u"% do ICMS Interestadual")
    icms_aliquota_inter_part = fields.Float(u'% Provisório de partilha do ICMS\
 Interestadual', default=40.0)
    icms_fcp_uf_dest = fields.Float(u'Valor do Fundo de Combate à Pobreza na \
UF de Destino')
    icms_uf_dest = fields.Float(u'Valor do ICMS da UF de Destino')
    icms_uf_remet = fields.Float(u'Valor do ICMS da UF Remetente')
    cest = fields.Char(string="CEST", size=10,
                       help="Código Especificador da Substituição Tributária")
