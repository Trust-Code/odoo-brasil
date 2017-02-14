# -*- coding: utf-8 -*-
# © 2009  Renato Lima - Akretion
# © 2012  Raphaël Valyi - Akretion
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api
from odoo.addons import decimal_precision as dp


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.depends('order_line.price_total', 'order_line.valor_desconto')
    def _amount_all(self):
        super(SaleOrder, self)._amount_all()
        for order in self:
            price_total = sum(l.price_total for l in order.order_line)
            price_subtotal = sum(l.price_subtotal for l in order.order_line)
            order.update({
                'total_tax': price_total - price_subtotal,
                'total_desconto': sum(l.valor_desconto
                                      for l in order.order_line),
                'total_bruto': sum(l.valor_bruto
                                   for l in order.order_line),
            })

    @api.multi
    def _prepare_invoice(self):
        res = super(SaleOrder, self)._prepare_invoice()
        if self.fiscal_position_id and self.fiscal_position_id.account_id:
            res['account_id'] = self.fiscal_position_id.account_id.id
        if self.fiscal_position_id and self.fiscal_position_id.journal_id:
            res['journal_id'] = self.fiscal_position_id.journal_id.id
        if self.fiscal_position_id.fiscal_observation_ids:
            res['fiscal_observation_ids'] = [
                (6, None, self.fiscal_position_id.fiscal_observation_ids.ids)]
        return res

    total_bruto = fields.Float(
        string='Total Bruto ( = )', readonly=True, compute='_amount_all',
        digits=dp.get_precision('Account'), store=True)
    total_tax = fields.Float(
        string='Impostos ( + )', readonly=True, compute='_amount_all',
        digits=dp.get_precision('Account'), store=True)
    total_desconto = fields.Float(
        string='Desconto Total ( - )', readonly=True, compute='_amount_all',
        digits=dp.get_precision('Account'), store=True,
        help="The discount amount.")


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    def _prepare_tax_context(self):
        return {
            'incluir_ipi_base': self.incluir_ipi_base,
            'icms_st_aliquota_mva': self.icms_st_aliquota_mva,
            'aliquota_icms_proprio': self.aliquota_icms_proprio,
            'icms_aliquota_reducao_base': self.icms_aliquota_reducao_base,
            'icms_st_aliquota_reducao_base':
            self.icms_st_aliquota_reducao_base,
            'ipi_reducao_bc': self.ipi_reducao_bc,
            'icms_st_aliquota_deducao': self.icms_st_aliquota_deducao,
        }

    @api.depends('product_uom_qty', 'discount', 'price_unit', 'tax_id',
                 'icms_st_aliquota_mva', 'incluir_ipi_base',
                 'icms_aliquota_reducao_base', 'icms_st_aliquota_reducao_base',
                 'ipi_reducao_bc', 'icms_st_aliquota_deducao')
    def _compute_amount(self):
        for line in self:
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            ctx = line._prepare_tax_context()
            tax_ids = line.tax_id.with_context(**ctx)
            taxes = tax_ids.compute_all(
                price, line.order_id.currency_id,
                line.product_uom_qty, product=line.product_id,
                partner=line.order_id.partner_id)

            valor_bruto = line.price_unit * line.product_uom_qty
            desconto = valor_bruto * line.discount / 100.0
            desconto = line.order_id.pricelist_id.currency_id.round(desconto)
            line.update({
                'price_tax': taxes['total_included'] - taxes['total_excluded'],
                'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
                'valor_bruto': valor_bruto,
                'valor_desconto': desconto,
            })

    @api.depends('cfop_id', 'icms_st_aliquota_mva', 'aliquota_icms_proprio',
                 'incluir_ipi_base', 'icms_aliquota_reducao_base', 'tem_difal',
                 'icms_st_aliquota_reducao_base', 'ipi_reducao_bc',
                 'icms_st_aliquota_deducao')
    def _compute_detalhes(self):
        for line in self:
            msg = []
            if line.cfop_id:
                msg += [u'CFOP: %s' % line.cfop_id.code]
            msg += [u'IPI na base ICMS: %s' % (
                u'Sim' if line.incluir_ipi_base else u'Não')]
            if line.icms_st_aliquota_mva:
                msg += [u'MVA (%%): %.2f' % line.icms_st_aliquota_mva]
            if line.aliquota_icms_proprio:
                msg += [u'ICMS Intra (%%): %.2f' % line.aliquota_icms_proprio]
            if line.icms_aliquota_reducao_base:
                msg += [u'Red. Base ICMS (%%): %.2f' %
                        line.icms_aliquota_reducao_base]
            if line.icms_st_aliquota_reducao_base:
                msg += [u'Red. Base ICMS ST (%%): %.2f' %
                        line.icms_st_aliquota_reducao_base]
            if line.ipi_reducao_bc:
                msg += [u'Red. Base IPI (%%): %.2f' % line.ipi_reducao_bc]

            line.detalhes_calculo = u'\n'.join(msg)

    icms_rule_id = fields.Many2one(
        'account.fiscal.position.tax.rule', 'Regra ICMS')
    ipi_rule_id = fields.Many2one(
        'account.fiscal.position.tax.rule', 'Regra IPI')
    pis_rule_id = fields.Many2one(
        'account.fiscal.position.tax.rule', 'Regra PIS')
    cofins_rule_id = fields.Many2one(
        'account.fiscal.position.tax.rule', 'Regra COFINS')
    issqn_rule_id = fields.Many2one(
        'account.fiscal.position.tax.rule', 'Regra ISSQN')
    ii_rule_id = fields.Many2one(
        'account.fiscal.position.tax.rule', 'Regra II')

    cfop_id = fields.Many2one('br_account.cfop', string="CFOP")

    icms_cst_normal = fields.Char(string="CST ICMS", size=5)
    icms_csosn_simples = fields.Char(string="CSOSN ICMS", size=5)
    icms_st_aliquota_mva = fields.Float(string=u'Alíquota MVA (%)',
                                        digits=dp.get_precision('Account'))
    aliquota_icms_proprio = fields.Float(
        string=u'Alíquota ICMS Próprio (%)',
        digits=dp.get_precision('Account'))
    incluir_ipi_base = fields.Boolean(string="Incluir IPI na Base ICMS")
    icms_aliquota_reducao_base = fields.Float(
        string=u'Redução Base ICMS (%)', digits=dp.get_precision('Account'))
    icms_st_aliquota_reducao_base = fields.Float(
        string=u'Redução Base ICMS ST(%)', digits=dp.get_precision('Account'))
    icms_st_aliquota_deducao = fields.Float(
        string=u"% Dedução", help="Alíquota interna ou interestadual aplicada \
         sobre o valor da operação para deduzir do ICMS ST - Para empresas \
         do Simples Nacional", digits=dp.get_precision('Account'))
    tem_difal = fields.Boolean(string="Possui Difal")

    ipi_cst = fields.Char(string='CST IPI', size=5)
    ipi_reducao_bc = fields.Float(
        string=u'Redução Base IPI (%)', digits=dp.get_precision('Account'))

    pis_cst = fields.Char(string='CST PIS', size=5)
    cofins_cst = fields.Char(string='CST COFINS', size=5)

    valor_desconto = fields.Float(
        compute='_compute_amount', string='Vlr. Desc. (-)', store=True,
        digits=dp.get_precision('Sale Price'))
    valor_bruto = fields.Float(
        compute='_compute_amount', string='Vlr. Bruto', store=True,
        digits=dp.get_precision('Sale Price'))
    price_without_tax = fields.Float(
        compute='_compute_amount', string=u'Preço Base', store=True,
        digits=dp.get_precision('Sale Price'))

    detalhes_calculo = fields.Text(
        string=u"Detalhes Cálculo", compute='_compute_detalhes', store=True)

    def _update_tax_from_ncm(self):
        if self.product_id:
            ncm = self.product_id.fiscal_classification_id
            taxes = ncm.tax_icms_st_id | ncm.tax_ipi_id
            self.update({
                'icms_st_aliquota_mva': ncm.icms_st_aliquota_mva,
                'icms_st_aliquota_reducao_base':
                ncm.icms_st_aliquota_reducao_base,
                'ipi_cst': ncm.ipi_cst,
                'ipi_reducao_bc': ncm.ipi_reducao_bc,
                'tax_id': [(6, None, [x.id for x in taxes if x])]
            })

    @api.multi
    def _compute_tax_id(self):
        res = super(SaleOrderLine, self)._compute_tax_id()
        for line in self:
            line._update_tax_from_ncm()
            fpos = line.order_id.fiscal_position_id or \
                line.order_id.partner_id.property_account_position_id
            if fpos:
                vals = fpos.map_tax_extra_values(
                    line.company_id, line.product_id, line.order_id.partner_id)

                for key, value in vals.iteritems():
                    if value and key in line._fields:
                        line.update({key: value})

                empty = line.env['account.tax'].browse()
                ipi = line.tax_id.filtered(lambda x: x.domain == 'ipi')
                icmsst = line.tax_id.filtered(lambda x: x.domain == 'icmsst')
                tax_ids = vals.get('tax_icms_id', empty) | \
                    vals.get('tax_icms_st_id', icmsst) | \
                    vals.get('tax_icms_inter_id', empty) | \
                    vals.get('tax_icms_intra_id', empty) | \
                    vals.get('tax_icms_fcp_id', empty) | \
                    vals.get('tax_simples_id', empty) | \
                    vals.get('tax_ipi_id', ipi) | \
                    vals.get('tax_pis_id', empty) | \
                    vals.get('tax_cofins_id', empty) | \
                    vals.get('tax_ii_id', empty) | \
                    vals.get('tax_issqn_id', empty)

                line.update({
                    'tax_id': [(6, None, [x.id for x in tax_ids if x])]
                })

        return res

    @api.multi
    def _prepare_invoice_line(self, qty):
        res = super(SaleOrderLine, self)._prepare_invoice_line(qty)

        res['valor_desconto'] = self.valor_desconto
        res['valor_bruto'] = self.valor_bruto

        # Improve this one later
        icms = self.tax_id.filtered(lambda x: x.domain == 'icms')
        icmsst = self.tax_id.filtered(lambda x: x.domain == 'icmsst')
        icms_inter = self.tax_id.filtered(lambda x: x.domain == 'icms_inter')
        icms_intra = self.tax_id.filtered(lambda x: x.domain == 'icms_intra')
        icms_fcp = self.tax_id.filtered(lambda x: x.domain == 'icms_fcp')
        simples = self.tax_id.filtered(lambda x: x.domain == 'simples')
        ipi = self.tax_id.filtered(lambda x: x.domain == 'ipi')
        pis = self.tax_id.filtered(lambda x: x.domain == 'pis')
        cofins = self.tax_id.filtered(lambda x: x.domain == 'cofins')
        ii = self.tax_id.filtered(lambda x: x.domain == 'ii')
        issqn = self.tax_id.filtered(lambda x: x.domain == 'issqn')

        res['icms_cst_normal'] = self.icms_cst_normal
        res['icms_csosn_simples'] = self.icms_csosn_simples

        res['tax_icms_id'] = icms and icms.id or False
        res['tax_icms_st_id'] = icmsst and icmsst.id or False
        res['tax_icms_inter_id'] = icms_inter and icms_inter.id or False
        res['tax_icms_intra_id'] = icms_intra and icms_intra.id or False
        res['tax_icms_fcp_id'] = icms_fcp and icms_fcp.id or False
        res['tax_simples_id'] = simples and simples.id or False
        res['tax_ipi_id'] = ipi and ipi.id or False
        res['tax_pis_id'] = pis and pis.id or False
        res['tax_cofins_id'] = cofins and cofins.id or False
        res['tax_ii_id'] = ii and ii.id or False
        res['tax_issqn_id'] = issqn and issqn.id or False

        res['product_type'] = self.product_id.fiscal_type
        res['company_fiscal_type'] = self.company_id.fiscal_type
        res['cfop_id'] = self.cfop_id.id
        ncm = self.product_id.fiscal_classification_id
        service = self.product_id.service_type_id
        res['fiscal_classification_id'] = ncm.id
        res['service_type_id'] = service.id
        res['icms_origem'] = self.product_id.origin

        if self.product_id.fiscal_type == 'service':
            res['tributos_estimados_federais'] = \
                self.product_id.lst_price * (service.federal_nacional / 100)
            res['tributos_estimados_estaduais'] = \
                self.product_id.lst_price * (service.estadual_imposto / 100)
            res['tributos_estimados_municipais'] = \
                self.product_id.lst_price * (service.municipal_imposto / 100)
        else:
            federal = ncm.federal_nacional if self.product_id.origin in \
                ('1', '2', '3', '8') else ncm.federal_importado

            res['tributos_estimados_federais'] = \
                self.product_id.lst_price * (federal / 100)
            res['tributos_estimados_estaduais'] = \
                self.product_id.lst_price * (ncm.estadual_imposto / 100)
            res['tributos_estimados_municipais'] = \
                self.product_id.lst_price * (ncm.municipal_imposto / 100)

        res['tributos_estimados'] = res['tributos_estimados_federais'] + \
            res['tributos_estimados_estaduais'] + \
            res['tributos_estimados_municipais']

        res['incluir_ipi_base'] = self.incluir_ipi_base
        res['icms_aliquota'] = icms.amount or 0.0
        res['icms_st_aliquota_mva'] = self.icms_st_aliquota_mva
        res['icms_st_aliquota'] = icmsst.amount or 0.0
        res['icms_aliquota_reducao_base'] = self.icms_aliquota_reducao_base
        res['icms_st_aliquota_reducao_base'] = \
            self.icms_st_aliquota_reducao_base
        res['icms_st_aliquota_deducao'] = self.icms_st_aliquota_deducao
        res['tem_difal'] = self.tem_difal
        res['icms_uf_remet'] = icms_inter.amount or 0.0
        res['icms_uf_dest'] = icms_intra.amount or 0.0
        res['icms_fcp_uf_dest'] = icms_fcp.amount or 0.0

        res['ipi_cst'] = self.ipi_cst
        res['ipi_aliquota'] = ipi.amount or 0.0
        res['ipi_reducao_bc'] = self.ipi_reducao_bc

        res['pis_cst'] = self.pis_cst
        res['pis_aliquota'] = pis.amount or 0.0

        res['cofins_cst'] = self.cofins_cst
        res['cofins_aliquota'] = cofins.amount or 0.0

        res['issqn_aliquota'] = issqn.amount or 0.0

        res['ii_aliquota'] = ii.amount or 0.0
        return res
