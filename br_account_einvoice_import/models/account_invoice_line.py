from odoo import api, fields, models
from odoo.addons import decimal_precision as dp


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    valor_bruto_manual = fields.Float(
        string='Vlr. Bruto Manual', store=True, digits=dp.get_precision('Account'))
    price_subtotal_manual = fields.Float(
        string='Subtotal Manual', store=True, digits=dp.get_precision('Account'))
    price_total_manual = fields.Float(
        string='Total Manual', store=True, digits=dp.get_precision('Account'))

    @api.one
    @api.depends('price_unit', 'discount', 'invoice_line_tax_ids', 'quantity',
                 'product_id', 'invoice_id.partner_id',
                 'invoice_id.currency_id', 'invoice_id.company_id',
                 'tax_icms_id', 'tax_icms_st_id', 'tax_icms_inter_id',
                 'tax_icms_intra_id', 'tax_icms_fcp_id', 'tax_ipi_id',
                 'tax_pis_id', 'tax_cofins_id', 'tax_ii_id', 'tax_issqn_id',
                 'tax_csll_id', 'tax_irrf_id', 'tax_inss_id',
                 'incluir_ipi_base', 'tem_difal', 'icms_aliquota_reducao_base',
                 'ipi_reducao_bc', 'icms_st_aliquota_mva',
                 'icms_st_aliquota_reducao_base', 'icms_aliquota_credito',
                 'icms_st_aliquota_deducao', 'icms_st_base_calculo_manual',
                 'icms_base_calculo_manual', 'ipi_base_calculo_manual',
                 'pis_base_calculo_manual', 'cofins_base_calculo_manual',
                 'icms_st_aliquota_deducao', 'ii_base_calculo',
                 'icms_aliquota_inter_part', 'desoneracao_icms', 'price_total_manual',
                 'price_subtotal_manual', 'valor_bruto_manual')
    def _compute_price(self):
        super(AccountInvoiceLine, self)._compute_price()
        manual_update = {}
        if self.valor_bruto_manual > 0:
            manual_update['valor_bruto'] = self.valor_bruto_manual
        if self.price_subtotal_manual > 0:
            manual_update['price_subtotal'] = self.price_subtotal_manual
        if self.price_total_manual > 0:
            manual_update['price_total'] = self.price_total_manual

        self.update(manual_update)