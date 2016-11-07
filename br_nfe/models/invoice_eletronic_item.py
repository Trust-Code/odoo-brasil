# -*- coding: utf-8 -*-
# © 2016 Alessandro Fernandes Martini, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class InvoiceEletronicItem(models.Model):
    _inherit = "invoice.eletronic.item"

    @api.multi
    @api.depends('icms_cst', 'origem')
    def _compute_cst_danfe(self):
        for item in self:
            item.cst_danfe = item.origem + item.icms_cst

    cst_danfe = fields.Char(string="CST Danfe", compute="_compute_cst_danfe")

    cest = fields.Char(string="CEST", size=10,
                       help="Código Especificador da Substituição Tributária")

    # ----------- ICMS INTERESTADUAL -----------
    tem_difal = fields.Boolean(u'Difal?')
    icms_bc_uf_dest = fields.Float(u'Base ICMS')
    icms_aliquota_fcp_uf_dest = fields.Float(u'% FCP')
    icms_aliquota_uf_dest = fields.Float(u'% ICMS destino')
    icms_aliquota_interestadual = fields.Float(u"% ICMS Inter")
    icms_aliquota_inter_part = fields.Float(u'% Partilha', default=40.0)
    icms_uf_remet = fields.Float(u'ICMS Remetente')
    icms_uf_dest = fields.Float(u'ICMS Destino')
    icms_fcp_uf_dest = fields.Float(u'Valor FCP')
