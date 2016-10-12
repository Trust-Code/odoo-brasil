# -*- coding: utf-8 -*-
# © 2016 Alessandro Fernandes Martini, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class InvoiceEletronicItem(models.Model):
    _inherit = "invoice.eletronic.item"

    cest = fields.Char(string="CEST", size=10,
                       help="Código Especificador da Substituição Tributária")

    # ----------- ICMS INTERESTADUAL -----------
    has_icms_difal = fields.Boolean(u'Difal?')
    icms_bc_uf_dest = fields.Float(u'Base ICMS')
    icms_aliquota_fcp_uf_dest = fields.Float(u'% FCP')
    icms_aliquota_uf_dest = fields.Float(u'% ICMS destino')
    icms_aliquota_interestadual = fields.Float(u"% ICMS Inter")
    icms_aliquota_inter_part = fields.Float(u'% Partilha', default=40.0)
    icms_fcp_uf_dest = fields.Float(u'Valor FCP')
    icms_uf_dest = fields.Float(u'ICMS Destino')
    icms_uf_remet = fields.Float(u'ICMS Remetente')
