# -*- coding: utf-8 -*-
# © 2009 Renato Lima - Akretion
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import api, fields, models
from odoo.addons import decimal_precision as dp
from odoo.addons.br_account.models.cst import CST_ICMS
from odoo.addons.br_account.models.cst import CSOSN_SIMPLES
from odoo.addons.br_account.models.cst import CST_IPI
from odoo.addons.br_account.models.cst import CST_PIS_COFINS
from odoo.addons.br_account.models.cst import ORIGEM_PROD
from odoo.addons.br_account.models.res_company import COMPANY_FISCAL_TYPE


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    @api.model
    def _default_company_fiscal_type(self):
        if self.invoice_id:
            return self.invoice_id.company_id.fiscal_type
        company = self.env['res.company'].browse(self.env.user.company_id.id)
        return company.fiscal_type

    @api.one
    @api.depends('price_unit', 'discount', 'invoice_line_tax_ids', 'quantity',
                 'product_id', 'invoice_id.partner_id',
                 'invoice_id.currency_id', 'invoice_id.company_id')
    def _compute_price(self):

        currency = self.invoice_id and self.invoice_id.currency_id or None
        price = self.price_unit * (1 - (self.discount or 0.0) / 100.0)
        taxes = False
        if self.invoice_line_tax_ids:
            tax_ids = self.invoice_line_tax_ids.with_context(
                incluir_ipi_base=True, aliquota_mva=self.icms_st_aliquota_mva)
            taxes = tax_ids.compute_all(
                price, currency, self.quantity, product=self.product_id,
                partner=self.invoice_id.partner_id)

        subtotal = price_subtotal_signed = taxes['total_excluded'] if taxes else self.quantity * price
        total = taxes['total_included'] if taxes else self.quantity * price
        without_tax = taxes['price_without_tax'] if taxes else self.quantity * price

        icms = sum(x['amount'] for x in taxes['taxes'] if x['id'] == self.tax_icms_id.id) if taxes else 0.0
        icmsst = sum(x['amount'] for x in taxes['taxes'] if x['id'] == self.tax_icms_st_id.id) if taxes else 0.0
        ipi = sum(x['amount'] for x in taxes['taxes'] if x['id'] == self.tax_ipi_id.id) if taxes else 0.0
        pis = sum(x['amount'] for x in taxes['taxes'] if x['id'] == self.tax_pis_id.id) if taxes else 0.0
        cofins = sum(x['amount'] for x in taxes['taxes'] if x['id'] == self.tax_cofins_id.id) if taxes else 0.0
        issqn = sum(x['amount'] for x in taxes['taxes'] if x['id'] == self.tax_issqn_id.id) if taxes else 0.0
        ii = sum(x['amount'] for x in taxes['taxes'] if x['id'] == self.tax_ii_id.id) if taxes else 0.0

        if self.invoice_id.currency_id and self.invoice_id.currency_id != self.invoice_id.company_id.currency_id:
            price_subtotal_signed = self.invoice_id.currency_id.compute(price_subtotal_signed, self.invoice_id.company_id.currency_id)
        sign = self.invoice_id.type in ['in_refund', 'out_refund'] and -1 or 1

        price_subtotal_signed = price_subtotal_signed * sign

        self.update({
            'price_total': total,
            'price_without_tax': without_tax,
            'price_subtotal': subtotal,
            'price_subtotal_signed': price_subtotal_signed,
            'valor_bruto': self.quantity * self.price_unit,
            'valor_desconto': self.valor_bruto * (self.discount / 100),
            'icms_valor': icms,
            'icms_st_valor': icmsst,
            'ipi_valor': ipi,
            'pis_valor': pis,
            'cofins_valor': cofins,
            'issqn_valor': issqn,
            'ii_valor': ii,
        })

    @api.onchange('quantity', 'price_unit', 'discount')
    def _recompute_tax_values(self):
        if self.calculate_tax:
            base_icms = base = self.quantity * self.price_unit
            self.ipi_base_calculo = base
            self.ipi_valor = base * self.ipi_aliquota
            self.pis_base_calculo = base
            self.pis_valor = base * self.cofins_aliquota
            self.cofins_base_calculo = base
            self.cofins_value = base * self.cofins_aliquota
            self.issqn_base_calculo = base
            self.issqn_valor = base * self.issqn_aliquota
            self.ii_base_calculo = base
            self.ii_valor = base * self.ii_aliquota

            if self.incluir_ipi_base:
                base_icms += self.ipi_base * self.ipi_percent
            base_icms -= self.valor_desconto

            self.icms_base_calculo = base_icms * (1 - self.icms_aliquota_reducao_base / 100)
            self.icms_valor = self.icms_base_calculo * (self.icms_aliquota / 100)

            self.icms_st_base = base * self.icms_st_aliquota_mva * \
                (1 - self.icms_st_aliquota_reducao_base / 100)

            self.icms_st_value = self.icms_valor - \
                (self.icms_st_base_calculo * self.icms_st_aliquota)

    @api.multi
    @api.depends('icms_cst_normal', 'icms_csosn_simples',
                 'company_fiscal_type')
    def _compute_cst_icms(self):
        for item in self:
            item.icms_cst = item.icms_cst_normal \
                if item.company_fiscal_type == '3' else item.icms_csosn_simples

    price_without_tax = fields.Float(
        compute='_compute_price', string='Preço Base', store=True,
        digits=dp.get_precision('Sale Price'))
    price_total = fields.Float(
        'Valor Líquido', digits=dp.get_precision('Account'), store=True,
        default=0.00, compute='_compute_price')
    valor_desconto = fields.Float(
        string='Vlr. desconto', store=True, compute='_compute_price',
        digits=dp.get_precision('Account'))
    valor_bruto = fields.Float(
        string='Vlr. Bruto', store=True, compute='_compute_price',
        digits=dp.get_precision('Account'))
    tributos_estimados = fields.Float(
        string='Total Estimado de Tributos', requeried=True, default=0.00,
        digits=dp.get_precision('Account'))

    rule_id = fields.Many2one('account.fiscal.position.tax.rule', 'Regra')
    cfop_id = fields.Many2one('br_account.cfop', 'CFOP')
    fiscal_classification_id = fields.Many2one(
        'product.fiscal.classification', 'Classificação Fiscal')
    product_type = fields.Selection(
        [('product', 'Produto'), ('service', 'Serviço')],
        string='Tipo do Produto', required=True, default='product')
    company_fiscal_type = fields.Selection(
        COMPANY_FISCAL_TYPE,
        default=_default_company_fiscal_type, string="Regime Tributário")
    calculate_tax = fields.Boolean(string="Calcular Imposto?", default=True)
    fiscal_comment = fields.Text(u'Observação Fiscal')

    # =========================================================================
    # ICMS Normal
    # =========================================================================
    tax_icms_id = fields.Many2one('account.tax', string="Alíquota ICMS",
                                  domain=[('domain', '=', 'icms')])
    icms_cst = fields.Char('CST ICMS', size=10,
                           store=True, compute='_compute_cst_icms')
    icms_cst_normal = fields.Selection(CST_ICMS, string="CST ICMS")
    icms_origem = fields.Selection(ORIGEM_PROD, 'Origem', default='0')
    icms_tipo_base = fields.Selection(
        [('0', '0- Margem Valor Agregado (%)'),
         ('1', '1 - Pauta (valor)'),
         ('2', '2 - Preço Tabelado Máximo (valor)'),
         ('3', '3 - Valor da Operação')],
        'Tipo Base ICMS', required=True, default='3')
    incluir_ipi_base = fields.Boolean(
        string="Incl. Valor Ipi?",
        help="Se marcado o valor do IPI inclui a base de cálculo")
    icms_base_calculo = fields.Float(
        'Base ICMS', required=True,
        digits=dp.get_precision('Account'), default=0.00)
    icms_valor = fields.Float(
        'Valor ICMS', required=True, compute='_compute_price', store=True,
        digits=dp.get_precision('Account'), default=0.00)
    icms_aliquota = fields.Float(
        'Perc ICMS', digits=dp.get_precision('Discount'), default=0.00)
    icms_aliquota_reducao_base = fields.Float(
        '% Red. Base ICMS', digits=dp.get_precision('Discount'),
        default=0.00)

    # =========================================================================
    # ICMS Substituição
    # =========================================================================
    tax_icms_st_id = fields.Many2one('account.tax', string="Alíquota ICMS ST",
                                     domain=[('domain', '=', 'icmsst')])
    icms_st_tipo_base = fields.Selection(
        [('0', '0- Preço tabelado ou máximo  sugerido'),
         ('1', '1 - Lista Negativa (valor)'),
         ('2', '2 - Lista Positiva (valor)'),
         ('3', '3 - Lista Neutra (valor)'),
         ('4', '4 - Margem Valor Agregado (%)'), ('5', '5 - Pauta (valor)')],
        'Tipo Base ICMS ST', required=True, default='4')
    icms_st_valor = fields.Float(
        'Valor ICMS ST', required=True, compute='_compute_price', store=True,
        digits=dp.get_precision('Account'), default=0.00)
    icms_st_base_calculo = fields.Float(
        'Base ICMS ST', required=True,
        digits=dp.get_precision('Account'), default=0.00)
    icms_st_aliquota = fields.Float(
        '% ICMS ST', digits=dp.get_precision('Discount'),
        default=0.00)
    icms_st_aliquota_reducao_base = fields.Float(
        '% Red. Base ST',
        digits=dp.get_precision('Discount'))
    icms_st_aliquota_mva = fields.Float(
        'MVA Ajustado ST',
        digits=dp.get_precision('Discount'), default=0.00)

    # =========================================================================
    # ICMS Difal
    # =========================================================================
    has_icms_difal = fields.Boolean(
        u'Difal?', digits=dp.get_precision('Discount'))
    icms_bc_uf_dest = fields.Float(
        u'Base ICMS', digits=dp.get_precision('Discount'))
    icms_aliquota_fcp_uf_dest = fields.Float(
        u'% FCP', digits=dp.get_precision('Discount'))
    icms_aliquota_uf_dest = fields.Float(
        u'% ICMS destino', digits=dp.get_precision('Discount'))
    icms_aliquota_interestadual = fields.Float(
        u"% ICMS Inter", digits=dp.get_precision('Discount'))
    icms_aliquota_inter_part = fields.Float(
        u'% Partilha', default=40.0, digits=dp.get_precision('Discount'))
    icms_fcp_uf_dest = fields.Float(
        u'Valor FCP', digits=dp.get_precision('Discount'))
    icms_uf_dest = fields.Float(
        u'ICMS Destino', digits=dp.get_precision('Discount'))
    icms_uf_remet = fields.Float(
        u'ICMS Remetente', digits=dp.get_precision('Discount'))

    # =========================================================================
    # ICMS Simples Nacional
    # =========================================================================
    icms_csosn_simples = fields.Selection(CSOSN_SIMPLES, string="CSOSN ICMS")
    icms_aliquota_credito = fields.Float(u"% Cŕedito ICMS")
    icms_valor_credito = fields.Float(u"Valor de Crédito")

    # =========================================================================
    # ISSQN
    # =========================================================================
    tax_issqn_id = fields.Many2one('account.tax', string="Alíquota ISSQN",
                                   domain=[('domain', '=', 'issqn')])
    issqn_tipo = fields.Selection(
        [('N', 'Normal'), ('R', 'Retida'),
         ('S', 'Substituta'), ('I', 'Isenta')], 'Tipo do ISSQN',
        required=True, default='N')
    service_type_id = fields.Many2one(
        'br_account.service.type', 'Tipo de Serviço')
    issqn_base_calculo = fields.Float(
        'Base ISSQN', required=True, digits=dp.get_precision('Account'),
        default=0.00)
    issqn_aliquota = fields.Float(
        'Perc ISSQN', required=True, digits=dp.get_precision('Discount'),
        default=0.00)
    issqn_valor = fields.Float(
        'Valor ISSQN', required=True, digits=dp.get_precision('Account'),
        default=0.00, compute='_compute_price', store=True)

    # =========================================================================
    # IPI
    # =========================================================================
    tax_ipi_id = fields.Many2one('account.tax', string="Alíquota IPI",
                                 domain=[('domain', '=', 'ipi')])
    ipi_tipo = fields.Selection(
        [('percent', 'Percentual'), ('quantity', 'Em Valor')],
        'Tipo do IPI', required=True, default='percent')
    ipi_base_calculo = fields.Float(
        'Base IPI', required=True, digits=dp.get_precision('Account'),
        default=0.00)
    ipi_reducao_bc = fields.Float(
        '% Redução Base', required=True, digits=dp.get_precision('Account'),
        default=0.00)
    ipi_valor = fields.Float(
        'Valor IPI', required=True, digits=dp.get_precision('Account'),
        default=0.00, compute='_compute_price', store=True)
    ipi_aliquota = fields.Float(
        'Perc IPI', required=True, digits=dp.get_precision('Discount'),
        default=0.00)
    ipi_cst = fields.Selection(CST_IPI, string='CST IPI')

    # =========================================================================
    # PIS
    # =========================================================================
    tax_pis_id = fields.Many2one('account.tax', string="Alíquota PIS",
                                 domain=[('domain', '=', 'pis')])
    pis_cst = fields.Selection(CST_PIS_COFINS, 'CST PIS')
    pis_tipo = fields.Selection(
        [('percent', 'Percentual'), ('quantity', 'Em Valor')],
        'Tipo do PIS', required=True, default='percent')
    pis_base_calculo = fields.Float(
        'Base PIS', required=True,
        digits=dp.get_precision('Account'), default=0.00)
    pis_valor = fields.Float(
        'Valor PIS', required=True, digits=dp.get_precision('Account'),
        default=0.00, compute='_compute_price', store=True)
    pis_aliquota = fields.Float(
        'Perc PIS', required=True, digits=dp.get_precision('Discount'),
        default=0.00)

    pis_st_tipo = fields.Selection(
        [('percent', 'Percentual'), ('quantity', 'Em Valor')],
        'Tipo do PIS ST', required=True, default='percent')
    pis_st_base_calculo = fields.Float(
        'Base PIS ST', required=True, digits=dp.get_precision('Account'),
        default=0.00)
    pis_st_aliquota = fields.Float(
        'Perc PIS ST', required=True, digits=dp.get_precision('Account'),
        default=0.00)
    pis_st_valor = fields.Float(
        'Valor PIS ST', required=True, digits=dp.get_precision('Account'),
        default=0.00)

    # =========================================================================
    # COFINS
    # =========================================================================
    tax_cofins_id = fields.Many2one('account.tax', string="Alíquota COFINS",
                                    domain=[('domain', '=', 'cofins')])
    cofins_cst = fields.Selection(CST_PIS_COFINS, 'CST PIS')
    cofins_tipo = fields.Selection(
        [('percent', 'Percentual'), ('quantity', 'Em Valor')],
        'Tipo do COFINS', required=True, default='percent')
    cofins_base_calculo = fields.Float(
        'Base COFINS',
        required=True,
        digits=dp.get_precision('Account'),
        default=0.00)
    cofins_valor = fields.Float(
        'Valor COFINS', required=True, digits=dp.get_precision('Account'),
        default=0.00, compute='_compute_price', store=True)
    cofins_aliquota = fields.Float(
        'Perc COFINS', required=True, digits=dp.get_precision('Discount'),
        default=0.00)
    cofins_st_tipo = fields.Selection(
        [('percent', 'Percentual'), ('quantity', 'Em Valor')],
        'Tipo do COFINS ST', required=True, default='percent')
    cofins_st_base_calculo = fields.Float(
        'Base COFINS ST', required=True, digits=dp.get_precision('Account'),
        default=0.00)
    cofins_st_aliquota = fields.Float(
        'Perc COFINS ST', required=True, digits=dp.get_precision('Discount'),
        default=0.00)
    cofins_st_valor = fields.Float(
        'Valor COFINS ST', required=True, digits=dp.get_precision('Account'),
        default=0.00)

    # =========================================================================
    # Imposto de importação
    # =========================================================================
    tax_ii_id = fields.Many2one('account.tax', string="Alíquota II",
                                domain=[('domain', '=', 'ii')])
    ii_base_calculo = fields.Float(
        'Base II', required=True, digits=dp.get_precision('Account'),
        default=0.00)
    ii_aliquota = fields.Float(
        '% II', required=True, digits=dp.get_precision('Account'),
        default=0.00)
    ii_valor = fields.Float(
        'Valor II', required=True, digits=dp.get_precision('Account'),
        default=0.00, compute='_compute_price', store=True)
    ii_valor_iof = fields.Float(
        'Valor IOF', required=True, digits=dp.get_precision('Account'),
        default=0.00)
    ii_valor_despesas = fields.Float(
        'Depesas Atuaneiras', required=True,
        digits=dp.get_precision('Account'), default=0.00)

    def _set_taxes(self):
        super(AccountInvoiceLine, self)._set_taxes()
        fpos = self.invoice_id.fiscal_position_id
        if fpos:
            vals = fpos.map_tax_extra_values(
                self.company_id, self.product_id, self.invoice_id.partner_id)

            for key, value in vals.iteritems():
                if value and key in self._fields:
                    self.update({key: value})

        self.invoice_line_tax_ids = self.tax_icms_id | \
            self.tax_ipi_id | self.tax_pis_id | self.tax_cofins_id | \
            self.tax_issqn_id | self.tax_ii_id | self.tax_icms_st_id

    @api.onchange('product_id')
    def _br_account_onchange_product_id(self):
        self.service_type_id = self.product_id.service_type_id.id
        self.product_type = self.product_id.fiscal_type
        self.fiscal_classification_id = \
            self.product_id.fiscal_classification_id.id
        self.tributos_estimados = self.price_subtotal * (
            self.fiscal_classification_id.federal_nacional +
            self.fiscal_classification_id.estadual_imposto +
            self.fiscal_classification_id.municipal_imposto) / 100

    def _update_invoice_line_ids(self):
        other_taxes = self.invoice_line_tax_ids.filtered(
            lambda x: not x.domain)
        self.invoice_line_tax_ids = other_taxes | self.tax_icms_id | \
            self.tax_ipi_id | self.tax_pis_id | self.tax_cofins_id | \
            self.tax_issqn_id | self.tax_ii_id | self.tax_icms_st_id

    @api.onchange('tax_icms_id')
    def _onchange_tax_icms_id(self):
        if self.tax_icms_id:
            self.icms_aliquota = self.tax_icms_id.amount
            self._update_invoice_line_ids()

    @api.onchange('tax_icms_st_id')
    def _onchange_tax_icms_st_id(self):
        if self.tax_icms_st_id:
            self.icms_st_aliquota = self.tax_icms_st_id.amount
            self._update_invoice_line_ids()

    @api.onchange('tax_pis_id')
    def _onchange_tax_pis_id(self):
        if self.tax_pis_id:
            self.pis_aliquota = self.tax_pis_id.amount
            self._update_invoice_line_ids()

    @api.onchange('tax_cofins_id')
    def _onchange_tax_cofins_id(self):
        if self.tax_cofins_id:
            self.cofins_aliquota = self.tax_cofins_id.amount
            self._update_invoice_line_ids()

    @api.onchange('tax_ipi_id')
    def _onchange_tax_ipi_id(self):
        if self.tax_ipi_id:
            self.ipi_aliquota = self.tax_ipi_id.amount
            self._update_invoice_line_ids()

    @api.onchange('tax_ii_id')
    def _onchange_tax_ii_id(self):
        if self.tax_ii_id:
            self.ii_aliquota = self.tax_ii_id.amount
            self._update_invoice_line_ids()
