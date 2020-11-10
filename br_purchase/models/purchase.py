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
                'l10n_br_total_tax': price_total - price_subtotal,
                'l10n_br_total_desconto': sum(l.l10n_br_valor_desconto
                                      for l in order.order_line),
                'l10n_br_total_bruto': sum(l.l10n_br_valor_bruto
                                           for l in order.order_line),
            })

    @api.multi
    def _prepare_invoice(self):
        res = super(PurchaseOrder, self)._prepare_invoice()
        if (self.fiscal_position_id and
                self.fiscal_position_id.l10n_br_account_id):
            res['account_id'] = self.fiscal_position_id.l10n_br_account_id.id
        if (self.fiscal_position_id and
                self.fiscal_position_id.l10n_br_journal_id):
            res['journal_id'] = self.fiscal_position_id.l10n_br_journal_id.id
        return res

    l10n_br_total_bruto = fields.Float(
        string='Total Bruto ( = )', readonly=True, compute='_amount_all',
        digits=dp.get_precision('Account'), store=True,
        oldname='total_bruto')
    l10n_br_total_tax = fields.Float(
        string='Impostos ( + )', readonly=True, compute='_amount_all',
        digits=dp.get_precision('Account'), store=True,
        oldname='total_tax')
    l10n_br_total_desconto = fields.Float(
        string='Desconto Total ( - )', readonly=True, compute='_amount_all',
        digits=dp.get_precision('Account'), store=True,
        help="The discount amount.", oldname='total_desconto')

    @api.onchange('fiscal_position_id')
    def _compute_tax_id(self):
        """
        Trigger the recompute of the taxes if the fiscal position is changed
        """
        for order in self:
            order.order_line._compute_tax_id()

    @api.onchange('partner_id')
    def onchange_partner_fpos(self):
        if not self.fiscal_position_id:
            fpos = self.partner_id.property_purchase_fiscal_position_id
            self.fiscal_position_id = fpos.id


class PurchaseOrderLine(models.Model):
    _name = 'purchase.order.line'
    _inherit = ['purchase.order.line', 'br.localization.filtering']

    def _prepare_tax_context(self):
        return {
            'l10n_br_incluir_ipi_base': self.l10n_br_incluir_ipi_base,
            'l10n_br_icms_st_aliquota_mva': self.l10n_br_icms_st_aliquota_mva,
            'l10n_br_aliquota_icms_proprio':
                self.l10n_br_aliquota_icms_proprio,
            'l10n_br_icms_aliquota_reducao_base':
                self.l10n_br_icms_aliquota_reducao_base,
            'l10n_br_icms_st_aliquota_reducao_base':
                self.l10n_br_icms_st_aliquota_reducao_base,
            'l10n_br_ipi_reducao_bc': self.l10n_br_ipi_reducao_bc,
            'l10n_br_icms_st_aliquota_deducao':
                self.l10n_br_icms_st_aliquota_deducao,
            'fiscal_type': self.l10n_br_fiscal_position_type,
        }

    @api.depends('taxes_id', 'product_qty', 'price_unit', 'l10n_br_discount',
                 'l10n_br_icms_aliquota_reducao_base',
                 'l10n_br_icms_st_aliquota_reducao_base',
                 'l10n_br_ipi_reducao_bc', 'l10n_br_icms_st_aliquota_deducao',
                 'l10n_br_incluir_ipi_base', 'l10n_br_icms_st_aliquota_mva')
    def _compute_amount(self):
        for line in self:
            price = line.price_unit * (1 - (line.l10n_br_discount or 0.0) / 100.0)
            ctx = line._prepare_tax_context()
            tax_ids = line.taxes_id.with_context(**ctx)
            taxes = tax_ids.compute_all(
                price, line.order_id.currency_id,
                line.product_qty, product=line.product_id,
                partner=line.order_id.partner_id)

            valor_bruto = line.price_unit * line.product_qty
            desconto = valor_bruto * line.l10n_br_discount / 100.0
            desconto = line.order_id.currency_id.round(desconto)

            line.update({
                'price_tax': taxes['total_included'] - taxes['total_excluded'],
                'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
                'l10n_br_valor_bruto': valor_bruto,
                'l10n_br_valor_desconto': desconto,
            })

    l10n_br_fiscal_position_type = fields.Selection(
        [('saida', 'Saída'), ('entrada', 'Entrada'),
         ('import', 'Entrada Importação')],
        string="Tipo da posição fiscal", oldname='fiscal_position_type')
    l10n_br_cfop_id = fields.Many2one('br_account.cfop', string="CFOP",
                                      oldname='cfop_id')

    l10n_br_icms_cst_normal = fields.Char(string="CST ICMS", size=5,
                                          oldname='icms_cst_normal')
    l10n_br_icms_csosn_simples = fields.Char(string="CSOSN ICMS", size=5,
                                             oldname='icms_csosn_simples')
    l10n_br_icms_st_aliquota_mva = fields.Float(
        string=u'Alíquota MVA (%)', digits=dp.get_precision('Account'),
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
    l10n_br_tem_difal = fields.Boolean(string="Possui Difal",
                                       oldname='tem_difal')

    l10n_br_ipi_cst = fields.Char(string='CST IPI', size=5, oldname='ipi_cst')
    l10n_br_ipi_reducao_bc = fields.Float(
        string=u'Redução Base IPI (%)', digits=dp.get_precision('Account'),
        oldname='ipi_reducao_bc')

    l10n_br_pis_cst = fields.Char(string='CST PIS', size=5, oldname='pis_cst')
    l10n_br_cofins_cst = fields.Char(string='CST COFINS', size=5,
                                     oldname='cofins_cst')
    l10n_br_issqn_deduction = fields.Float(string="% Dedução de base ISSQN",
                                           oldname='issqn_deduction')

    l10n_br_discount = fields.Float(
        string='Discount (%)',
        digits=dp.get_precision('Discount'),
        default=0.0,
        oldname='discount')

    l10n_br_valor_desconto = fields.Float(
        compute='_compute_amount', string=u'Vlr. Desc. (-)', store=True,
        digits=dp.get_precision('Sale Price'),
        oldname='valor_desconto')
    l10n_br_valor_bruto = fields.Float(
        compute='_compute_amount', string='Vlr. Bruto', store=True,
        digits=dp.get_precision('Sale Price'),
        oldname='valor_bruto')

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
                'taxes_id': [(6, None, [x.id for x in taxes if x])]
            })

    def _onchange_quantity(self):
        res = super(PurchaseOrderLine, self)._onchange_quantity()
        self._compute_tax_id()
        return res

    @api.multi
    def _compute_tax_id(self):
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
                ipi = line.taxes_id.filtered(
                    lambda x: x.l10n_br_domain == 'ipi')
                icmsst = line.taxes_id.filtered(
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
                    'taxes_id': [(6, None, [x.id for x in tax_ids if x])],
                    'l10n_br_fiscal_position_type': fpos.fiscal_type,
                })

    # Calcula o custo da mercadoria comprada
    @api.multi
    def _get_stock_move_price_unit(self):
        price = self.price_unit
        order = self.order_id
        ctx = self._prepare_tax_context()
        tax_ids = self.taxes_id.with_context(**ctx)
        taxes = tax_ids.compute_all(
            price,
            currency=self.order_id.currency_id,
            quantity=1.0,
            product=self.product_id,
            partner=self.order_id.partner_id)

        price = taxes['total_included']
        for tax in taxes['taxes']:
            # Quando o imposto não tem conta contábil, deduzimos que ele não é
            # recuperável e portanto somamos ao custo, como partimos do valor
            # já com imposto se existir conta diminuimos o valor deste imposto
            if tax['account_id'] and self.product_qty:
                price -= tax['amount'] / self.product_qty

        if self.product_uom.id != self.product_id.uom_id.id:
            price *= self.product_uom.factor / self.product_id.uom_id.factor
        if order.currency_id != order.company_id.currency_id:
            price = order.currency_id.compute(price,
                                              order.company_id.currency_id,
                                              round=False)
        return price
