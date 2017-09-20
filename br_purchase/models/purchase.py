# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api
from odoo.addons import decimal_precision as dp


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    @api.depends('order_line.price_total')
    def _amount_all(self):
        super(PurchaseOrder, self)._amount_all()
        for order in self:
            price_total = sum(l.price_total for l in order.order_line)
            price_subtotal = sum(l.price_subtotal for l in order.order_line)
            order.update({
                'amount_untaxed': price_subtotal,
                'amount_tax': price_total - price_subtotal,
                'amount_total': price_total,
                'total_tax': price_total - price_subtotal,
                'total_bruto': sum(l.valor_bruto
                                   for l in order.order_line),
            })

    @api.multi
    def _prepare_invoice(self):
        res = super(PurchaseOrder, self)._prepare_invoice()
        if self.fiscal_position_id and self.fiscal_position_id.account_id:
            res['account_id'] = self.fiscal_position_id.account_id.id
        if self.fiscal_position_id and self.fiscal_position_id.journal_id:
            res['journal_id'] = self.fiscal_position_id.journal_id.id
        return res

    total_bruto = fields.Float(
        string='Total Bruto ( = )', readonly=True, compute='_amount_all',
        digits=dp.get_precision('Account'), store=True)
    total_tax = fields.Float(
        string='Impostos ( + )', readonly=True, compute='_amount_all',
        digits=dp.get_precision('Account'), store=True)

    @api.onchange('fiscal_position_id')
    def _compute_tax_id(self):
        """
        Trigger the recompute of the taxes if the fiscal position is changed
        """
        for order in self:
            order.order_line._compute_tax_id()


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

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

    @api.depends('taxes_id', 'product_qty',  'price_unit',
                 'icms_aliquota_reducao_base', 'icms_st_aliquota_reducao_base',
                 'ipi_reducao_bc', 'icms_st_aliquota_deducao',
                 'incluir_ipi_base', 'icms_st_aliquota_mva')
    def _compute_amount(self):
        for line in self:
            price = line.price_unit
            ctx = line._prepare_tax_context()
            tax_ids = line.taxes_id.with_context(**ctx)
            taxes = tax_ids.compute_all(
                price, line.order_id.currency_id,
                line.product_qty, product=line.product_id,
                partner=line.order_id.partner_id)

            valor_bruto = line.price_unit * line.product_qty
            line.update({
                'price_tax': taxes['total_included'] - taxes['total_excluded'],
                'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
                'valor_bruto': valor_bruto,
            })

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
        string=u"% Dedução", help=u"Alíquota interna ou interestadual aplicada \
         sobre o valor da operação para deduzir do ICMS ST - Para empresas \
         do Simples Nacional", digits=dp.get_precision('Account'))
    tem_difal = fields.Boolean(string="Possui Difal")

    ipi_cst = fields.Char(string='CST IPI', size=5)
    ipi_reducao_bc = fields.Float(
        string=u'Redução Base IPI (%)', digits=dp.get_precision('Account'))

    pis_cst = fields.Char(string='CST PIS', size=5)
    cofins_cst = fields.Char(string='CST COFINS', size=5)

    valor_bruto = fields.Float(
        compute='_compute_amount', string='Vlr. Bruto', store=True,
        digits=dp.get_precision('Sale Price'))

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
                'taxes_id': [(6, None, [x.id for x in taxes if x])]
            })

    def _onchange_quantity(self):
        res = super(PurchaseOrderLine, self)._onchange_quantity()
        self._compute_tax_id()
        return res

    @api.multi
    def _compute_tax_id(self):
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
                ipi = line.taxes_id.filtered(lambda x: x.domain == 'ipi')
                icmsst = line.taxes_id.filtered(lambda x: x.domain == 'icmsst')
                tax_ids = vals.get('tax_icms_id', empty) | \
                    vals.get('tax_icms_st_id', icmsst) | \
                    vals.get('tax_icms_inter_id', empty) | \
                    vals.get('tax_icms_intra_id', empty) | \
                    vals.get('tax_icms_fcp_id', empty) | \
                    vals.get('tax_ipi_id', ipi) | \
                    vals.get('tax_pis_id', empty) | \
                    vals.get('tax_cofins_id', empty) | \
                    vals.get('tax_ii_id', empty) | \
                    vals.get('tax_issqn_id', empty)

                line.update({
                    'taxes_id': [(6, None, [x.id for x in tax_ids if x])]
                })

    # Calcula o custo da mercadoria comprada
    @api.multi
    def _get_stock_move_price_unit(self):
        price = self.price_unit
        ctx = self._prepare_tax_context()
        tax_ids = self.taxes_id.with_context(**ctx)
        taxes = tax_ids.compute_all(
            price, self.order_id.currency_id,
            self.product_qty, product=self.product_id,
            partner=self.order_id.partner_id)

        price = taxes['total_included']

        for tax in taxes['taxes']:
            # Quando o imposto não tem conta contábil, deduzimos que ele não é
            # recuperável e portanto somamos ao custo, como partimos do valor
            # já com imposto se existir conta diminuimos o valor deste imposto
            if tax['account_id']:
                price -= tax['amount']

        price = price / self.product_qty
        return price
