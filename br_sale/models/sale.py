# -*- coding: utf-8 -*-
# © 2009  Renato Lima - Akretion
# © 2012  Raphaël Valyi - Akretion
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from datetime import timedelta

from odoo import models, fields, api
from odoo.addons import decimal_precision as dp


class SaleOrder(models.Model):
    _name = 'sale.order'
    _inherit = ['sale.order', 'br.localization.filtering']

    @api.depends('order_line.price_total', 'order_line.l10n_br_valor_desconto')
    def _amount_all(self):
        super(SaleOrder, self)._amount_all()
        for order in self:
            price_total = sum(l.price_total for l in order.order_line)
            price_subtotal = sum(l.price_subtotal for l in order.order_line)
            order.update({
                'l10n_br_total_tax': price_total - price_subtotal,
                'l10n_br_total_ipi':
                    sum(l.l10n_br_ipi_valor for l in order.order_line),
                'l10n_br_total_icms_st': sum(l.l10n_br_icms_st_valor
                                             for l in order.order_line),
                'l10n_br_total_desconto': sum(l.l10n_br_valor_desconto
                                              for l in order.order_line),
                'l10n_br_total_bruto': sum(l.l10n_br_valor_bruto
                                           for l in order.order_line),
            })

    @api.multi
    def _prepare_invoice(self):
        res = super(SaleOrder, self)._prepare_invoice()
        if (self.fiscal_position_id and
                self.fiscal_position_id.l10n_br_account_id):
            res['account_id'] = self.fiscal_position_id.l10n_br_account_id.id
        if (self.fiscal_position_id and
                self.fiscal_position_id.l10n_br_journal_id):
            res['journal_id'] = self.fiscal_position_id.l10n_br_journal_id.id
        if self.fiscal_position_id.l10n_br_fiscal_observation_ids:
            res['l10n_br_fiscal_observation_ids'] = [
                (6, None,
                 self.fiscal_position_id.l10n_br_fiscal_observation_ids.ids)]
        if self.fiscal_position_id:
            fpos = self.fiscal_position_id
            res['l10n_br_product_document_id'] = \
                fpos.l10n_br_product_document_id.id
            res['l10n_br_product_serie_id'] = \
                fpos.l10n_br_product_serie_id.id
            res['l10n_br_service_document_id'] = \
                fpos.l10n_br_service_document_id.id
            res['l10n_br_service_serie_id'] = \
                fpos.l10n_br_service_serie_id.id
        return res

    l10n_br_total_bruto = fields.Float(
        string='Total Bruto ( = )', readonly=True, compute='_amount_all',
        digits=dp.get_precision('Account'), store=True, oldname='total_bruto')
    l10n_br_total_tax = fields.Float(
        string='Impostos ( + )', readonly=True, compute='_amount_all',
        digits=dp.get_precision('Account'), store=True, oldname='total_tax')
    l10n_br_total_ipi = fields.Float(
        string='IPI', readonly=True, compute='_amount_all',
        digits=dp.get_precision('Account'), store=True, oldname='total_ipi')
    l10n_br_total_icms_st = fields.Float(
        string='ICMS ST', readonly=True, compute='_amount_all',
        digits=dp.get_precision('Account'), store=True,
        oldname='total_icms_st')
    l10n_br_total_desconto = fields.Float(
        string='Desconto Total ( - )', readonly=True, compute='_amount_all',
        digits=dp.get_precision('Account'), store=True,
        help="The discount amount.", oldname='total_desconto')


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    def _prepare_tax_context(self):
        return {
            'incluir_ipi_base': self.l10n_br_incluir_ipi_base,
            'icms_st_aliquota_mva': self.l10n_br_icms_st_aliquota_mva,
            'aliquota_icms_proprio': self.l10n_br_aliquota_icms_proprio,
            'icms_aliquota_reducao_base':
                self.l10n_br_icms_aliquota_reducao_base,
            'icms_st_aliquota_reducao_base':
                self.l10n_br_icms_st_aliquota_reducao_base,
            'ipi_reducao_bc': self.l10n_br_ipi_reducao_bc,
            'icms_st_aliquota_deducao': self.l10n_br_icms_st_aliquota_deducao,
        }

    @api.multi
    def _prepare_order_line_procurement(self, group_id=False):
        vals = super(SaleOrderLine, self)._prepare_order_line_procurement(
            group_id=group_id)

        confirm = fields.Date.from_string(self.order_id.confirmation_date)
        vals["date_planned"] = confirm + timedelta(days=self.customer_lead)
        return vals

    @api.depends('product_uom_qty', 'discount', 'price_unit', 'tax_id',
                 'l10n_br_icms_st_aliquota_mva', 'l10n_br_incluir_ipi_base',
                 'l10n_br_icms_aliquota_reducao_base',
                 'l10n_br_icms_st_aliquota_reducao_base',
                 'l10n_br_ipi_reducao_bc', 'l10n_br_icms_st_aliquota_deducao')
    def _compute_amount(self):
        for line in self:
            ipi = 0.0
            icms_st = 0.0
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            ctx = line._prepare_tax_context()
            tax_ids = line.tax_id.with_context(**ctx)
            taxes = tax_ids.compute_all(
                price, line.order_id.currency_id,
                line.product_uom_qty, product=line.product_id,
                partner=line.order_id.partner_id)

            for tax in taxes['taxes']:
                tax_id = self.env['account.tax'].browse(tax['id'])
                if tax_id.l10n_br_domain == 'ipi':
                    ipi += tax['amount']
                if tax_id.l10n_br_domain == 'icmsst':
                    icms_st += tax['amount']

            valor_bruto = line.price_unit * line.product_uom_qty
            desconto = valor_bruto * line.discount / 100.0
            desconto = line.order_id.pricelist_id.currency_id.round(desconto)
            line.update({
                'price_tax': taxes['total_included'] - taxes['total_excluded'],
                'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
                'l10n_br_valor_bruto': valor_bruto,
                'l10n_br_valor_desconto': desconto,
                'l10n_br_icms_st_valor': icms_st,
                'l10n_br_ipi_valor': ipi,
            })

    @api.depends('l10n_br_cfop_id', 'l10n_br_icms_st_aliquota_mva',
                 'l10n_br_aliquota_icms_proprio', 'l10n_br_incluir_ipi_base',
                 'l10n_br_icms_aliquota_reducao_base', 'l10n_br_tem_difal',
                 'l10n_br_icms_st_aliquota_reducao_base',
                 'l10n_br_ipi_reducao_bc', 'l10n_br_icms_st_aliquota_deducao')
    def _compute_detalhes(self):
        for line in self:
            msg = []
            if line.l10n_br_cfop_id:
                msg += [u'CFOP: %s' % line.l10n_br_cfop_id.code]
            msg += [u'IPI na base ICMS: %s' % (
                u'Sim' if line.l10n_br_incluir_ipi_base else u'Não')]
            if line.l10n_br_icms_st_aliquota_mva:
                msg += [u'MVA (%%): %.2f' % line.l10n_br_icms_st_aliquota_mva]
            if line.l10n_br_aliquota_icms_proprio:
                msg += [u'ICMS Intra (%%): %.2f' %
                        line.l10n_br_aliquota_icms_proprio]
            if line.l10n_br_icms_aliquota_reducao_base:
                msg += [u'Red. Base ICMS (%%): %.2f' %
                        line.l10n_br_icms_aliquota_reducao_base]
            if line.l10n_br_icms_st_aliquota_reducao_base:
                msg += [u'Red. Base ICMS ST (%%): %.2f' %
                        line.icms_st_aliquota_reducao_base]
            if line.l10n_br_ipi_reducao_bc:
                msg += [u'Red. Base IPI (%%): %.2f' %
                        line.l10n_br_ipi_reducao_bc]

            line.l10n_br_detalhes_calculo = u'\n'.join(msg)

    l10n_br_icms_rule_id = fields.Many2one(
        'account.fiscal.position.tax.rule', u'Regra ICMS',
        oldname='icms_rule_id')
    l10n_br_ipi_rule_id = fields.Many2one(
        'account.fiscal.position.tax.rule', u'Regra IPI',
        oldname='ipi_rule_id')
    l10n_br_pis_rule_id = fields.Many2one(
        'account.fiscal.position.tax.rule', u'Regra PIS',
        oldname='pis_rule_id')
    l10n_br_cofins_rule_id = fields.Many2one(
        'account.fiscal.position.tax.rule', u'Regra COFINS',
        oldname='cofins_rule_id')
    l10n_br_issqn_rule_id = fields.Many2one(
        'account.fiscal.position.tax.rule', u'Regra ISSQN',
        oldname='issqn_rule_id')
    l10n_br_ii_rule_id = fields.Many2one(
        'account.fiscal.position.tax.rule', u'Regra II',
        oldname='ii_rule_id')

    l10n_br_cfop_id = fields.Many2one('br_account.cfop', string=u"CFOP",
                                      oldname='cfop_id')

    l10n_br_icms_cst_normal = fields.Char(string=u"CST ICMS", size=5,
                                          oldname='icms_cst_normal')
    l10n_br_icms_csosn_simples = fields.Char(string=u"CSOSN ICMS", size=5,
                                             oldname='icms_csosn_simples')
    l10n_br_icms_st_aliquota_mva = fields.Float(
        string=u'Alíquota MVA (%)',
        digits=dp.get_precision('Account'),
        oldname='icms_st_aliquota_mva')
    l10n_br_aliquota_icms_proprio = fields.Float(
        string=u'Alíquota ICMS Próprio (%)',
        digits=dp.get_precision('Account'), oldname='aliquota_icms_proprio')
    l10n_br_incluir_ipi_base = fields.Boolean(
        string="Incluir IPI na Base ICMS",
        oldname='incluir_ipi_base')
    l10n_br_icms_aliquota_reducao_base = fields.Float(
        string=u'Redução Base ICMS (%)', digits=dp.get_precision('Account'),
        oldname='icms_aliquota_reducao_base')
    l10n_br_icms_st_aliquota_reducao_base = fields.Float(
        string=u'Redução Base ICMS ST(%)', digits=dp.get_precision('Account'),
        oldname='icms_st_aliquota_reducao_base')
    l10n_br_icms_st_aliquota_deducao = fields.Float(
        string=u"% Dedução",
        help=u"Alíquota interna ou interestadual aplicada \
         sobre o valor da operação para deduzir do ICMS ST - Para empresas \
         do Simples Nacional", digits=dp.get_precision('Account'),
        oldname='icms_st_aliquota_deducao')
    l10n_br_icms_st_valor = fields.Monetary(
        string="Valor ICMS ST", store=True, compute='_compute_amount',
        digits=dp.get_precision('Sale Price'), oldname='icms_st_valor')
    l10n_br_tem_difal = fields.Boolean(string=u"Possui Difal",
                                       oldname='tem_difal')

    l10n_br_ipi_cst = fields.Char(string=u'CST IPI', size=5, oldname='ipi_cst')
    l10n_br_ipi_reducao_bc = fields.Float(
        string=u'Redução Base IPI (%)', digits=dp.get_precision('Account'),
        oldname='ipi_reducao_bc')
    l10n_br_ipi_valor = fields.Monetary(
        string="Valor IPI", store=True, compute='_compute_amount',
        digits=dp.get_precision('Sale Price'), oldname='ipi_valor')

    l10n_br_pis_cst = fields.Char(string=u'CST PIS', size=5, oldname='pis_cst')
    l10n_br_cofins_cst = fields.Char(
        string=u'CST COFINS', size=5,
        oldname='cofins_cst')
    l10n_br_issqn_deduction = fields.Float(
        string="% Dedução de base ISSQN",
        oldname='l10n_br_issqn_deduction')

    l10n_br_valor_desconto = fields.Float(
        compute='_compute_amount', string=u'Vlr. Desc. (-)', store=True,
        digits=dp.get_precision('Sale Price'), oldname='valor_desconto')
    l10n_br_valor_bruto = fields.Float(
        compute='_compute_amount', string=u'Vlr. Bruto', store=True,
        digits=dp.get_precision('Sale Price'), oldname='valor_bruto')
    l10n_br_price_without_tax = fields.Float(
        compute='_compute_amount', string=u'Preço Base', store=True,
        digits=dp.get_precision('Sale Price'), oldname='price_without_tax')

    l10n_br_detalhes_calculo = fields.Text(
        string=u"Detalhes Cálculo", compute='_compute_detalhes', store=True,
        oldname='detalhes_calculo')

    def _update_tax_from_ncm(self):
        if self.product_id:
            ncm = self.product_id.l10n_br_fiscal_classification_id
            taxes = ncm.tax_icms_st_id | ncm.tax_ipi_id
            self.update({
                'l10n_br_icms_st_aliquota_mva': ncm.icms_st_aliquota_mva,
                'l10n_br_icms_st_aliquota_reducao_base':
                ncm.icms_st_aliquota_reducao_base,
                'l10n_br_ipi_cst': ncm.ipi_cst,
                'l10n_br_ipi_reducao_bc': ncm.ipi_reducao_bc,
                'tax_id': [(6, None, [x.id for x in taxes if x])]
            })

    @api.multi
    def _compute_tax_id(self):
        res = super(SaleOrderLine, self)._compute_tax_id()
        for line in self.filtered(lambda x: x.l10n_br_localization):
            line._update_tax_from_ncm()
            fpos = line.order_id.fiscal_position_id or \
                line.order_id.partner_id.property_account_position_id
            if fpos:
                vals = fpos.map_tax_extra_values(
                    line.company_id, line.product_id, line.order_id.partner_id)

                for key, value in vals.items():
                    if value and key in line._fields:
                        line.update({key: value})

                empty = line.env['account.tax'].browse()
                ipi = line.tax_id.filtered(
                    lambda x: x.l10n_br_domain == 'ipi')
                icmsst = line.tax_id.filtered(
                    lambda x: x.l10n_br_domain == 'icmsst')
                tax_ids = vals.get('tax_icms_id', empty) | \
                    vals.get('tax_icms_st_id', icmsst) | \
                    vals.get('tax_icms_inter_id', empty) | \
                    vals.get('tax_icms_intra_id', empty) | \
                    vals.get('tax_icms_fcp_id', empty) | \
                    vals.get('tax_ipi_id', ipi) | \
                    vals.get('tax_pis_id', empty) | \
                    vals.get('tax_cofins_id', empty) | \
                    vals.get('tax_ii_id', empty) | \
                    vals.get('tax_issqn_id', empty) | \
                    vals.get('tax_csll_id', empty) | \
                    vals.get('tax_irrf_id', empty) | \
                    vals.get('tax_inss_id', empty)

                line.update({
                    'tax_id': [(6, None, [x.id for x in tax_ids if x])]
                })

        return res

    @api.multi
    def _prepare_invoice_line(self, qty):
        res = super(SaleOrderLine, self)._prepare_invoice_line(qty)

        res['l10n_br_valor_desconto'] = self.l10n_br_valor_desconto
        res['l10n_br_valor_bruto'] = self.l10n_br_valor_bruto

        # Improve this one later
        icms = self.tax_id.filtered(lambda x: x.l10n_br_domain == 'icms')
        icmsst = self.tax_id.filtered(lambda x: x.l10n_br_domain == 'icmsst')
        icms_inter = self.tax_id.filtered(
            lambda x: x.l10n_br_domain == 'icms_inter')
        icms_intra = self.tax_id.filtered(
            lambda x: x.l10n_br_domain == 'icms_intra')
        icms_fcp = self.tax_id.filtered(
            lambda x: x.l10n_br_domain == 'icms_fcp')
        ipi = self.tax_id.filtered(lambda x: x.l10n_br_domain == 'ipi')
        pis = self.tax_id.filtered(lambda x: x.l10n_br_domain == 'pis')
        cofins = self.tax_id.filtered(lambda x: x.l10n_br_domain == 'cofins')
        ii = self.tax_id.filtered(lambda x: x.l10n_br_domain == 'ii')
        issqn = self.tax_id.filtered(lambda x: x.l10n_br_domain == 'issqn')
        csll = self.tax_id.filtered(lambda x: x.l10n_br_domain == 'csll')
        inss = self.tax_id.filtered(lambda x: x.l10n_br_domain == 'inss')
        irrf = self.tax_id.filtered(lambda x: x.l10n_br_domain == 'irrf')

        res['l10n_br_icms_cst_normal'] = self.l10n_br_icms_cst_normal
        res['l10n_br_icms_csosn_simples'] = self.l10n_br_icms_csosn_simples

        res['l10n_br_tax_icms_id'] = icms and icms.id or False
        res['l10n_br_tax_icms_st_id'] = icmsst and icmsst.id or False
        res['l10n_br_tax_icms_inter_id'] = \
            icms_inter and icms_inter.id or False
        res['l10n_br_tax_icms_intra_id'] = \
            icms_intra and icms_intra.id or False
        res['l10n_br_tax_icms_fcp_id'] = icms_fcp and icms_fcp.id or False
        res['l10n_br_tax_ipi_id'] = ipi and ipi.id or False
        res['l10n_br_tax_pis_id'] = pis and pis.id or False
        res['l10n_br_tax_cofins_id'] = cofins and cofins.id or False
        res['l10n_br_tax_ii_id'] = ii and ii.id or False
        res['l10n_br_tax_issqn_id'] = issqn and issqn.id or False
        res['l10n_br_tax_csll_id'] = csll and csll.id or False
        res['l10n_br_tax_irrf_id'] = inss and inss.id or False
        res['l10n_br_tax_inss_id'] = irrf and irrf.id or False

        res['l10n_br_product_type'] = self.product_id.l10n_br_fiscal_type
        res['l10n_br_company_fiscal_type'] = self.\
            company_id.l10n_br_fiscal_type
        res['l10n_br_cfop_id'] = self.l10n_br_cfop_id.id
        ncm = self.product_id.l10n_br_fiscal_classification_id
        service = self.product_id.l10n_br_service_type_id
        res['l10n_br_fiscal_classification_id'] = ncm.id
        res['l10n_br_service_type_id'] = service.id
        res['l10n_br_icms_origem'] = self.product_id.l10n_br_origin

        if self.product_id.l10n_br_fiscal_type == 'service':
            res['l10n_br_tributos_estimados_federais'] = \
                self.price_subtotal * (service.federal_nacional / 100)
            res['l10n_br_tributos_estimados_estaduais'] = \
                self.price_subtotal * (service.estadual_imposto / 100)
            res['l10n_br_tributos_estimados_municipais'] = \
                self.price_subtotal * (service.municipal_imposto / 100)
        else:
            federal = ncm.federal_nacional \
                if self.product_id.l10n_br_origin in ('1', '2', '3', '8') \
                else ncm.federal_importado

            res['l10n_br_tributos_estimados_federais'] = \
                self.price_subtotal * (federal / 100)
            res['l10n_br_tributos_estimados_estaduais'] = \
                self.price_subtotal * (ncm.estadual_imposto / 100)
            res['l10n_br_tributos_estimados_municipais'] = \
                self.price_subtotal * (ncm.municipal_imposto / 100)

        res['l10n_br_tributos_estimados'] = (
            res['l10n_br_tributos_estimados_federais'] +
            res['l10n_br_tributos_estimados_estaduais'] +
            res['l10n_br_tributos_estimados_municipais']
        )

        res['l10n_br_incluir_ipi_base'] = self.l10n_br_incluir_ipi_base
        res['l10n_br_icms_aliquota'] = icms.amount or 0.0
        res['l10n_br_icms_st_aliquota_mva'] = self.l10n_br_icms_st_aliquota_mva
        res['l10n_br_icms_st_aliquota'] = icmsst.amount or 0.0
        res['l10n_br_icms_aliquota_reducao_base'] = self. \
            l10n_br_icms_aliquota_reducao_base
        res['l10n_br_icms_st_aliquota_reducao_base'] = self. \
            l10n_br_icms_st_aliquota_reducao_base
        res['l10n_br_icms_st_aliquota_deducao'] = self.\
            l10n_br_icms_st_aliquota_deducao
        res['l10n_br_tem_difal'] = self.l10n_br_tem_difal
        res['l10n_br_icms_uf_remet'] = icms_inter.amount or 0.0
        res['l10n_br_icms_uf_dest'] = icms_intra.amount or 0.0
        res['l10n_br_icms_fcp_uf_dest'] = icms_fcp.amount or 0.0

        res['l10n_br_ipi_cst'] = self.l10n_br_ipi_cst
        res['l10n_br_ipi_aliquota'] = ipi.amount or 0.0
        res['l10n_br_ipi_reducao_bc'] = self.l10n_br_ipi_reducao_bc

        res['l10n_br_pis_cst'] = self.l10n_br_pis_cst
        res['l10n_br_pis_aliquota'] = pis.amount or 0.0

        res['l10n_br_cofins_cst'] = self.l10n_br_cofins_cst
        res['l10n_br_cofins_aliquota'] = cofins.amount or 0.0

        res['l10n_br_issqn_aliquota'] = issqn.amount or 0.0
        res['l10n_br_issqn_deduction'] = self.l10n_br_issqn_deduction

        res['l10n_br_ii_aliquota'] = ii.amount or 0.0
        res['l10n_br_csll_aliquota'] = csll.amount or 0.0
        res['l10n_br_inss_aliquota'] = inss.amount or 0.0
        res['l10n_br_irrf_aliquota'] = irrf.amount or 0.0
        return res
