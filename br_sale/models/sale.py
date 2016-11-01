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
            'ipi_reducao_bc': self.ipi_reducao_bc
        }

    @api.depends('product_uom_qty', 'discount', 'price_unit', 'tax_id',
                 'icms_st_aliquota_mva', 'incluir_ipi_base',
                 'icms_aliquota_reducao_base', 'icms_st_aliquota_reducao_base',
                 'ipi_reducao_bc')
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
                 'incluir_ipi_base', 'icms_aliquota_reducao_base',
                 'icms_st_aliquota_reducao_base', 'ipi_reducao_bc')
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

    rule_id = fields.Many2one('account.fiscal.position.tax.rule', 'Regra')
    cfop_id = fields.Many2one('br_account.cfop', string="CFOP")

    icms_cst_normal = fields.Char(string="CST ICMS", size=5)
    icms_csosn_simples = fields.Char(string="CSOSN ICMS", size=5)
    icms_st_aliquota_mva = fields.Float(string='Alíquota MVA (%)',
                                        digits=dp.get_precision('Account'))
    aliquota_icms_proprio = fields.Float(
        string='Alíquota ICMS Próprio (%)', digits=dp.get_precision('Account'))
    incluir_ipi_base = fields.Boolean(string="Incluir Ipi na Base ICMS")
    icms_aliquota_reducao_base = fields.Float(
        string='Redução Base ICMS (%)', digits=dp.get_precision('Account'))
    icms_st_aliquota_reducao_base = fields.Float(
        string='Redução Base ICMS ST(%)', digits=dp.get_precision('Account'))

    ipi_cst = fields.Char(string='CST IPI', size=5)
    ipi_reducao_bc = fields.Float(
        string='Redução Base IPI (%)', digits=dp.get_precision('Account'))

    pis_cst = fields.Char(string='CST PIS', size=5)
    cofins_cst = fields.Char(string='CST COFINS', size=5)
    cofins_base_calculo = fields.Float(
        'Base COFINS', required=True, digits=dp.get_precision('Account'))

    valor_desconto = fields.Float(
        compute='_compute_amount', string='Vlr. Desc. (-)', store=True,
        digits=dp.get_precision('Sale Price'))
    valor_bruto = fields.Float(
        compute='_compute_amount', string='Vlr. Bruto', store=True,
        digits=dp.get_precision('Sale Price'))
    price_without_tax = fields.Float(
        compute='_compute_amount', string='Preço Base', store=True,
        digits=dp.get_precision('Sale Price'))

    detalhes_calculo = fields.Text(
        string="Detalhes Cálculo", compute='_compute_detalhes', store=True)

    @api.multi
    def _compute_tax_id(self):
        res = super(SaleOrderLine, self)._compute_tax_id()
        for line in self:
            fpos = line.order_id.fiscal_position_id or \
                line.order_id.partner_id.property_account_position_id
            if fpos:
                vals = fpos.map_tax_extra_values(
                    line.company_id, line.product_id, line.order_id.partner_id)

                for key, value in vals.iteritems():
                    if value and key in line._fields:
                        line.update({key: value})

                tax_ids = [vals.get('tax_icms_id', False),
                           vals.get('tax_icms_st_id', False),
                           vals.get('tax_ipi_id', False),
                           vals.get('tax_pis_id', False),
                           vals.get('tax_cofins_id', False),
                           vals.get('tax_ii_id', False),
                           vals.get('tax_issqn_id', False)]
                line.update({
                    'tax_id': [(6, None, [x.id for x in tax_ids if x])]
                })

        return res

    @api.multi
    def _prepare_invoice_line(self, qty):
        res = super(SaleOrderLine, self)._prepare_invoice_line(qty)

        res['valor_desconto'] = self.valor_desconto
        res['valor_bruto'] = self.valor_bruto
        icms = self.tax_id.filtered(lambda x: x.domain == 'icms')
        icmsst = self.tax_id.filtered(lambda x: x.domain == 'icmsst')
        ipi = self.tax_id.filtered(lambda x: x.domain == 'ipi')
        pis = self.tax_id.filtered(lambda x: x.domain == 'pis')
        cofins = self.tax_id.filtered(lambda x: x.domain == 'cofins')
        ii = self.tax_id.filtered(lambda x: x.domain == 'ii')
        issqn = self.tax_id.filtered(lambda x: x.domain == 'issqn')

        res['icms_cst_normal'] = self.icms_cst_normal
        res['icms_csosn_simples'] = self.icms_csosn_simples

        res['tax_icms_id'] = icms and icms.id or False
        res['tax_icms_st_id'] = icmsst and icmsst.id or False
        res['tax_ipi_id'] = ipi and ipi.id or False
        res['tax_pis_id'] = pis and pis.id or False
        res['tax_cofins_id'] = cofins and cofins.id or False
        res['tax_ii_id'] = ii and ii.id or False
        res['tax_issqn_id'] = issqn and issqn.id or False

        res['cfop_id'] = self.cfop_id.id
        res['fiscal_classification_id'] = \
            self.product_id.fiscal_classification_id.id
        res['service_type_id'] = self.product_id.service_type_id.id

        res['incluir_ipi_base'] = self.incluir_ipi_base
        res['icms_aliquota'] = icms.amount or 0.0
        res['icms_st_aliquota_mva'] = self.icms_st_aliquota_mva
        res['icms_st_aliquota'] = icmsst.amount or 0.0
        res['icms_aliquota_reducao_base'] = self.icms_aliquota_reducao_base
        res['icms_st_aliquota_reducao_base'] = \
            self.icms_st_aliquota_reducao_base

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
