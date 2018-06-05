# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    def _prepare_invoice_line_from_po_line(self, line):
        res = super(AccountInvoice, self)._prepare_invoice_line_from_po_line(
            line)
        res['valor_bruto'] = line.valor_bruto

        # Improve this one later
        icms = line.taxes_id.filtered(lambda x: x.domain == 'icms')
        icmsst = line.taxes_id.filtered(lambda x: x.domain == 'icmsst')
        icms_inter = line.taxes_id.filtered(lambda x: x.domain == 'icms_inter')
        icms_intra = line.taxes_id.filtered(lambda x: x.domain == 'icms_intra')
        icms_fcp = line.taxes_id.filtered(lambda x: x.domain == 'icms_fcp')
        ipi = line.taxes_id.filtered(lambda x: x.domain == 'ipi')
        pis = line.taxes_id.filtered(lambda x: x.domain == 'pis')
        cofins = line.taxes_id.filtered(lambda x: x.domain == 'cofins')
        ii = line.taxes_id.filtered(lambda x: x.domain == 'ii')
        issqn = line.taxes_id.filtered(lambda x: x.domain == 'issqn')
        csll = line.taxes_id.filtered(lambda x: x.domain == 'csll')
        inss = line.taxes_id.filtered(lambda x: x.domain == 'inss')
        irrf = line.taxes_id.filtered(lambda x: x.domain == 'irrf')

        res['icms_cst_normal'] = line.icms_cst_normal
        res['icms_csosn_simples'] = line.icms_csosn_simples

        res['tax_icms_id'] = icms and icms.id or False
        res['tax_icms_st_id'] = icmsst and icmsst.id or False
        res['tax_icms_inter_id'] = icms_inter and icms_inter.id or False
        res['tax_icms_intra_id'] = icms_intra and icms_intra.id or False
        res['tax_icms_fcp_id'] = icms_fcp and icms_fcp.id or False
        res['tax_ipi_id'] = ipi and ipi.id or False
        res['tax_pis_id'] = pis and pis.id or False
        res['tax_cofins_id'] = cofins and cofins.id or False
        res['tax_ii_id'] = ii and ii.id or False
        res['tax_issqn_id'] = issqn and issqn.id or False
        res['tax_csll_id'] = csll and csll.id or False
        res['tax_irrf_id'] = inss and inss.id or False
        res['tax_inss_id'] = irrf and irrf.id or False

        res['product_type'] = line.product_id.fiscal_type
        res['company_fiscal_type'] = line.company_id.fiscal_type
        res['cfop_id'] = line.cfop_id.id
        ncm = line.product_id.fiscal_classification_id
        service = line.product_id.service_type_id
        res['fiscal_classification_id'] = ncm.id
        res['service_type_id'] = service.id
        res['icms_origem'] = line.product_id.origin

        valor = 0
        if line.product_id.fiscal_type == 'service':
            valor = line.product_id.lst_price * (
                service.federal_nacional + service.estadual_imposto +
                service.municipal_imposto) / 100
        else:
            nacional = ncm.federal_nacional if line.product_id.origin in \
                ('1', '2', '3', '8') else ncm.federal_importado
            valor = line.product_id.lst_price * (
                nacional + ncm.estadual_imposto +
                ncm.municipal_imposto) / 100

        res['tributos_estimados'] = valor

        res['incluir_ipi_base'] = line.incluir_ipi_base
        res['icms_tipo_base'] = '3'
        res['icms_aliquota'] = icms.amount or 0.0
        res['icms_st_tipo_base'] = '4'
        res['icms_st_aliquota_mva'] = line.icms_st_aliquota_mva
        res['icms_st_aliquota'] = icmsst.amount or 0.0
        res['icms_aliquota_reducao_base'] = line.icms_aliquota_reducao_base
        res['icms_st_aliquota_reducao_base'] = \
            line.icms_st_aliquota_reducao_base
        res['icms_st_aliquota_deducao'] = line.icms_st_aliquota_deducao
        res['tem_difal'] = line.tem_difal
        res['icms_uf_remet'] = icms_inter.amount or 0.0
        res['icms_uf_dest'] = icms_intra.amount or 0.0
        res['icms_fcp_uf_dest'] = icms_fcp.amount or 0.0

        res['ipi_cst'] = line.ipi_cst
        res['ipi_aliquota'] = ipi.amount or 0.0
        res['ipi_reducao_bc'] = line.ipi_reducao_bc
        res['ipi_tipo'] = 'percent'

        res['pis_cst'] = line.pis_cst
        res['pis_aliquota'] = pis.amount or 0.0
        res['pis_tipo'] = 'percent'

        res['cofins_cst'] = line.cofins_cst
        res['cofins_aliquota'] = cofins.amount or 0.0
        res['cofins_tipo'] = 'percent'

        res['issqn_aliquota'] = issqn.amount or 0.0
        res['issqn_tipo'] = 'N'
        res['l10n_br_issqn_deduction'] = line.l10n_br_issqn_deduction

        res['ii_aliquota'] = ii.amount or 0.0

        res['csll_aliquota'] = csll.amount or 0.0
        res['inss_aliquota'] = inss.amount or 0.0
        res['irrf_aliquota'] = irrf.amount or 0.0
        return res
