# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    def _prepare_invoice_line_from_po_line(self, line):
        res = super(AccountInvoice, self)._prepare_invoice_line_from_po_line(
            line)
        res['l10n_br_valor_bruto'] = line.l10n_br_valor_bruto

        # Improve this one later
        icms = line.taxes_id.filtered(lambda x: x.l10n_br_domain == 'icms')
        icmsst = line.taxes_id.filtered(lambda x: x.l10n_br_domain == 'icmsst')
        icms_inter = line.taxes_id.filtered(
            lambda x: x.l10n_br_domain == 'icms_inter')
        icms_intra = line.taxes_id.filtered(
            lambda x: x.l10n_br_domain == 'icms_intra')
        icms_fcp = line.taxes_id.filtered(
            lambda x: x.l10n_br_domain == 'icms_fcp')
        ipi = line.taxes_id.filtered(lambda x: x.l10n_br_domain == 'ipi')
        pis = line.taxes_id.filtered(lambda x: x.l10n_br_domain == 'pis')
        cofins = line.taxes_id.filtered(lambda x: x.l10n_br_domain == 'cofins')
        ii = line.taxes_id.filtered(lambda x: x.l10n_br_domain == 'ii')
        issqn = line.taxes_id.filtered(lambda x: x.l10n_br_domain == 'issqn')
        csll = line.taxes_id.filtered(lambda x: x.l10n_br_domain == 'csll')
        inss = line.taxes_id.filtered(lambda x: x.l10n_br_domain == 'inss')
        irrf = line.taxes_id.filtered(lambda x: x.l10n_br_domain == 'irrf')

        res['l10n_br_icms_cst_normal'] = line.l10n_br_icms_cst_normal
        res['l10n_br_icms_csosn_simples'] = line.l10n_br_icms_csosn_simples

        res['l10n_br_tax_icms_id'] = icms and icms.id or False
        res['l10n_br_tax_icms_st_id'] = icmsst and icmsst.id or False
        res['l10n_br_tax_icms_inter_id'] = icms_inter and icms_inter.id or False
        res['l10n_br_tax_icms_intra_id'] = icms_intra and icms_intra.id or False
        res['l10n_br_tax_icms_fcp_id'] = icms_fcp and icms_fcp.id or False
        res['l10n_br_tax_ipi_id'] = ipi and ipi.id or False
        res['l10n_br_tax_pis_id'] = pis and pis.id or False
        res['l10n_br_tax_cofins_id'] = cofins and cofins.id or False
        res['l10n_br_tax_ii_id'] = ii and ii.id or False
        res['l10n_br_tax_issqn_id'] = issqn and issqn.id or False
        res['l10n_br_tax_csll_id'] = csll and csll.id or False
        res['l10n_br_tax_irrf_id'] = inss and inss.id or False
        res['l10n_br_tax_inss_id'] = irrf and irrf.id or False

        res['l10n_br_product_type'] = line.product_id.l10n_br_fiscal_type
        res['l10n_br_company_fiscal_type'] = line.company_id.l10n_br_fiscal_type
        res['l10n_br_cfop_id'] = line.l10n_br_cfop_id.id
        ncm = line.product_id.l10n_br_fiscal_classification_id
        service = line.product_id.l10n_br_service_type_id
        res['l10n_br_fiscal_classification_id'] = ncm.id
        res['l10n_br_service_type_id'] = service.id
        res['l10n_br_icms_origem'] = line.product_id.l10n_br_origin

        valor = 0
        if line.product_id.l10n_br_fiscal_type == 'service':
            valor = line.product_id.lst_price * (
                service.federal_nacional + service.estadual_imposto +
                service.municipal_imposto) / 100
        else:
            nacional = ncm.federal_nacional \
                if line.product_id.l10n_br_origin in \
                ('1', '2', '3', '8') else ncm.federal_importado
            valor = line.product_id.lst_price * (
                nacional + ncm.estadual_imposto +
                ncm.municipal_imposto) / 100

        res['l10n_br_tributos_estimados'] = valor

        res['l10n_br_incluir_ipi_base'] = line.l10n_br_incluir_ipi_base
        res['l10n_br_icms_tipo_base'] = '3'
        res['l10n_br_icms_aliquota'] = icms.amount or 0.0
        res['l10n_br_icms_st_tipo_base'] = '4'
        res['l10n_br_icms_st_aliquota_mva'] = line.l10n_br_icms_st_aliquota_mva
        res['l10n_br_icms_st_aliquota'] = icmsst.amount or 0.0
        res['l10n_br_icms_aliquota_reducao_base'] = \
            line.l10n_br_icms_aliquota_reducao_base
        res['l10n_br_icms_st_aliquota_reducao_base'] = \
            line.l10n_br_icms_st_aliquota_reducao_base
        res['l10n_br_icms_st_aliquota_deducao'] = \
            line.l10n_br_icms_st_aliquota_deducao
        res['l10n_br_tem_difal'] = line.l10n_br_tem_difal
        res['l10n_br_icms_uf_remet'] = icms_inter.amount or 0.0
        res['l10n_br_icms_uf_dest'] = icms_intra.amount or 0.0
        res['l10n_br_icms_fcp_uf_dest'] = icms_fcp.amount or 0.0

        res['l10n_br_ipi_cst'] = line.l10n_br_ipi_cst
        res['l10n_br_ipi_aliquota'] = ipi.amount or 0.0
        res['l10n_br_ipi_reducao_bc'] = line.l10n_br_ipi_reducao_bc
        res['l10n_br_ipi_tipo'] = 'percent'

        res['l10n_br_pis_cst'] = line.l10n_br_pis_cst
        res['l10n_br_pis_aliquota'] = pis.amount or 0.0
        res['l10n_br_pis_tipo'] = 'percent'

        res['l10n_br_cofins_cst'] = line.l10n_br_cofins_cst
        res['l10n_br_cofins_aliquota'] = cofins.amount or 0.0
        res['l10n_br_cofins_tipo'] = 'percent'

        res['l10n_br_issqn_aliquota'] = issqn.amount or 0.0
        res['l10n_br_issqn_tipo'] = 'N'
        res['l10n_br_issqn_deduction'] = line.l10n_br_issqn_deduction

        res['l10n_br_ii_aliquota'] = ii.amount or 0.0

        res['l10n_br_csll_aliquota'] = csll.amount or 0.0
        res['l10n_br_inss_aliquota'] = inss.amount or 0.0
        res['l10n_br_irrf_aliquota'] = irrf.amount or 0.0
        return res
