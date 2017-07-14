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

    def _prepare_tax_context(self):
        return {
            'incluir_ipi_base': self.incluir_ipi_base,
            'icms_st_aliquota_mva': self.icms_st_aliquota_mva,
            'icms_aliquota_reducao_base': self.icms_aliquota_reducao_base,
            'icms_st_aliquota_reducao_base':
            self.icms_st_aliquota_reducao_base,
            'icms_st_aliquota_deducao': self.icms_st_aliquota_deducao,
            'ipi_reducao_bc': self.ipi_reducao_bc,
            'icms_base_calculo': self.icms_base_calculo,
            'ipi_base_calculo': self.ipi_base_calculo,
            'pis_base_calculo': self.pis_base_calculo,
            'cofins_base_calculo': self.cofins_base_calculo,
            'ii_base_calculo': self.ii_base_calculo,
            'issqn_base_calculo': self.issqn_base_calculo,
        }

    @api.one
    @api.depends('price_unit', 'discount', 'invoice_line_tax_ids', 'quantity',
                 'product_id', 'invoice_id.partner_id',
                 'invoice_id.currency_id', 'invoice_id.company_id',
                 'tax_icms_id', 'tax_icms_st_id', 'tax_icms_inter_id',
                 'tax_icms_intra_id', 'tax_icms_fcp_id', 'tax_ipi_id',
                 'tax_pis_id', 'tax_cofins_id', 'tax_ii_id', 'tax_issqn_id',
                 'tax_csll_id', 'tax_irrf_id', 'tax_inss_id',
                 'incluir_ipi_base', 'tem_difal', 'icms_aliquota_reducao_base',
                 'ipi_reducao_bc', 'icms_st_aliquota_mva', 'tax_simples_id',
                 'icms_st_aliquota_reducao_base', 'icms_aliquota_credito',
                 'icms_st_aliquota_deducao')
    def _compute_price(self):
        currency = self.invoice_id and self.invoice_id.currency_id or None
        price = self.price_unit * (1 - (self.discount or 0.0) / 100.0)

        valor_bruto = self.price_unit * self.quantity
        desconto = valor_bruto * self.discount / 100.0
        subtotal = valor_bruto - desconto

        taxes = False
        self._update_invoice_line_ids()
        if self.invoice_line_tax_ids:
            ctx = self._prepare_tax_context()

            tax_ids = self.invoice_line_tax_ids.with_context(**ctx)

            taxes = tax_ids.compute_all(
                price, currency, self.quantity, product=self.product_id,
                partner=self.invoice_id.partner_id)

        icms = ([x for x in taxes['taxes']
                 if x['id'] == self.tax_icms_id.id]) if taxes else []
        icmsst = ([x for x in taxes['taxes']
                   if x['id'] == self.tax_icms_st_id.id]) if taxes else []
        icms_inter = (
            [x for x in taxes['taxes']
             if x['id'] == self.tax_icms_inter_id.id]) if taxes else []
        icms_intra = (
            [x for x in taxes['taxes']
             if x['id'] == self.tax_icms_intra_id.id]) if taxes else []
        icms_fcp = ([x for x in taxes['taxes']
                    if x['id'] == self.tax_icms_fcp_id.id]) if taxes else []
        simples = ([x for x in taxes['taxes']
                    if x['id'] == self.tax_simples_id.id]) if taxes else []
        ipi = ([x for x in taxes['taxes']
                if x['id'] == self.tax_ipi_id.id]) if taxes else []
        pis = ([x for x in taxes['taxes']
                if x['id'] == self.tax_pis_id.id]) if taxes else []
        cofins = ([x for x in taxes['taxes']
                   if x['id'] == self.tax_cofins_id.id]) if taxes else []
        issqn = ([x for x in taxes['taxes']
                  if x['id'] == self.tax_issqn_id.id]) if taxes else []
        ii = ([x for x in taxes['taxes']
               if x['id'] == self.tax_ii_id.id]) if taxes else []
        csll = ([x for x in taxes['taxes']
                if x['id'] == self.tax_csll_id.id]) if taxes else []
        irrf = ([x for x in taxes['taxes']
                if x['id'] == self.tax_irrf_id.id]) if taxes else []
        inss = ([x for x in taxes['taxes']
                if x['id'] == self.tax_inss_id.id]) if taxes else []

        price_subtotal_signed = taxes['total_excluded'] if taxes else subtotal
        if self.invoice_id.currency_id and self.invoice_id.currency_id != \
           self.invoice_id.company_id.currency_id:
            price_subtotal_signed = self.invoice_id.currency_id.compute(
                price_subtotal_signed, self.invoice_id.company_id.currency_id)
        sign = self.invoice_id.type in ['in_refund', 'out_refund'] and -1 or 1

        price_subtotal_signed = price_subtotal_signed * sign
        self.update({
            'price_total': taxes['total_included'] if taxes else subtotal,
            'price_tax': taxes['total_included'] - taxes['total_excluded']
            if taxes else 0,
            'price_subtotal': taxes['total_excluded'] if taxes else subtotal,
            'price_subtotal_signed': price_subtotal_signed,
            'valor_bruto': self.quantity * self.price_unit,
            'valor_desconto': desconto,
            'icms_base_calculo': sum([x['base'] for x in icms]),
            'icms_valor': sum([x['amount'] for x in icms]),
            'icms_st_base_calculo': sum([x['base'] for x in icmsst]),
            'icms_st_valor': sum([x['amount'] for x in icmsst]),
            'icms_bc_uf_dest': sum([x['base'] for x in icms_inter]),
            'icms_uf_remet': sum([x['amount'] for x in icms_inter]),
            'icms_uf_dest': sum([x['amount'] for x in icms_intra]),
            'icms_fcp_uf_dest': sum([x['amount'] for x in icms_fcp]),
            'icms_valor_credito': sum([x['base'] for x in simples]) *
            (self.icms_aliquota_credito / 100),
            'ipi_base_calculo': sum([x['base'] for x in ipi]),
            'ipi_valor': sum([x['amount'] for x in ipi]),
            'pis_base_calculo': sum([x['base'] for x in pis]),
            'pis_valor': sum([x['amount'] for x in pis]),
            'cofins_base_calculo': sum([x['base'] for x in cofins]),
            'cofins_valor': sum([x['amount'] for x in cofins]),
            'issqn_base_calculo': sum([x['base'] for x in issqn]),
            'issqn_valor': sum([x['amount'] for x in issqn]),
            'ii_base_calculo': sum([x['base'] for x in ii]),
            'ii_valor': sum([x['amount'] for x in ii]),
            'csll_base_calculo': sum([x['base'] for x in csll]),
            'csll_valor': sum([x['amount'] for x in csll]),
            'inss_base_calculo': sum([x['base'] for x in inss]),
            'inss_valor': sum([x['amount'] for x in inss]),
            'irrf_base_calculo': sum([x['base'] for x in irrf]),
            'irrf_valor': sum([x['amount'] for x in irrf]),
        })

    @api.multi
    @api.depends('icms_cst_normal', 'icms_csosn_simples',
                 'company_fiscal_type')
    def _compute_cst_icms(self):
        for item in self:
            item.icms_cst = item.icms_cst_normal \
                if item.company_fiscal_type == '3' else item.icms_csosn_simples

    price_tax = fields.Float(
        compute='_compute_price', string='Impostos', store=True,
        digits=dp.get_precision('Account'))
    price_total = fields.Float(
        u'Valor Líquido', digits=dp.get_precision('Account'), store=True,
        default=0.00, compute='_compute_price')
    valor_desconto = fields.Float(
        string='Vlr. desconto', store=True, compute='_compute_price',
        digits=dp.get_precision('Account'))
    valor_bruto = fields.Float(
        string='Vlr. Bruto', store=True, compute='_compute_price',
        digits=dp.get_precision('Account'))
    tributos_estimados = fields.Float(
        string='Total Est. Tributos', default=0.00,
        digits=dp.get_precision('Account'))
    tributos_estimados_federais = fields.Float(
        string='Tributos Federais', default=0.00,
        digits=dp.get_precision('Account'))
    tributos_estimados_estaduais = fields.Float(
        string='Tributos Estaduais', default=0.00,
        digits=dp.get_precision('Account'))
    tributos_estimados_municipais = fields.Float(
        string='Tributos Municipais', default=0.00,
        digits=dp.get_precision('Account'))

    rule_id = fields.Many2one('account.fiscal.position.tax.rule', 'Regra')
    cfop_id = fields.Many2one('br_account.cfop', 'CFOP')
    fiscal_classification_id = fields.Many2one(
        'product.fiscal.classification', u'Classificação Fiscal')
    product_type = fields.Selection(
        [('product', 'Produto'), ('service', u'Serviço')],
        string='Tipo do Produto', required=True, default='product')
    company_fiscal_type = fields.Selection(
        COMPANY_FISCAL_TYPE,
        default=_default_company_fiscal_type, string=u"Regime Tributário")
    calculate_tax = fields.Boolean(string="Calcular Imposto?", default=True)
    fiscal_comment = fields.Text(u'Observação Fiscal')

    # =========================================================================
    # ICMS Normal
    # =========================================================================
    icms_rule_id = fields.Many2one('account.fiscal.position.tax.rule', 'Regra')
    tax_icms_id = fields.Many2one('account.tax', string=u"Alíquota ICMS",
                                  domain=[('domain', '=', 'icms')])
    icms_cst = fields.Char('CST ICMS', size=10,
                           store=True, compute='_compute_cst_icms')
    icms_cst_normal = fields.Selection(CST_ICMS, string="CST ICMS")
    icms_origem = fields.Selection(ORIGEM_PROD, 'Origem', default='0')
    icms_tipo_base = fields.Selection(
        [('0', u'0 - Margem Valor Agregado (%)'),
         ('1', u'1 - Pauta (valor)'),
         ('2', u'2 - Preço Tabelado Máximo (valor)'),
         ('3', u'3 - Valor da Operação')],
        'Tipo Base ICMS', required=True, default='3')
    incluir_ipi_base = fields.Boolean(
        string="Incl. Valor IPI?",
        help=u"Se marcado o valor do IPI inclui a base de cálculo")
    icms_base_calculo = fields.Float(
        'Base ICMS', required=True, compute='_compute_price', store=True,
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
    tax_icms_st_id = fields.Many2one('account.tax', string=u"Alíquota ICMS ST",
                                     domain=[('domain', '=', 'icmsst')])
    icms_st_tipo_base = fields.Selection(
        [('0', u'0 - Preço tabelado ou máximo  sugerido'),
         ('1', u'1 - Lista Negativa (valor)'),
         ('2', u'2 - Lista Positiva (valor)'),
         ('3', u'3 - Lista Neutra (valor)'),
         ('4', u'4 - Margem Valor Agregado (%)'),
         ('5', u'5 - Pauta (valor)')],
        'Tipo Base ICMS ST', required=True, default='4')
    icms_st_valor = fields.Float(
        'Valor ICMS ST', required=True, compute='_compute_price', store=True,
        digits=dp.get_precision('Account'), default=0.00)
    icms_st_base_calculo = fields.Float(
        'Base ICMS ST', required=True, compute='_compute_price', store=True,
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
    tem_difal = fields.Boolean(
        u'Difal?', digits=dp.get_precision('Discount'))
    icms_bc_uf_dest = fields.Float(
        u'Base ICMS', compute='_compute_price',
        digits=dp.get_precision('Discount'))
    tax_icms_inter_id = fields.Many2one(
        'account.tax', help=u"Alíquota utilizada na operação Interestadual",
        string="ICMS Inter", domain=[('domain', '=', 'icms_inter')])
    tax_icms_intra_id = fields.Many2one(
        'account.tax', help=u"Alíquota interna do produto no estado destino",
        string="ICMS Intra", domain=[('domain', '=', 'icms_intra')])
    tax_icms_fcp_id = fields.Many2one(
        'account.tax', string="% FCP", domain=[('domain', '=', 'fcp')])
    icms_aliquota_inter_part = fields.Float(
        u'% Partilha', default=40.0, digits=dp.get_precision('Discount'))
    icms_fcp_uf_dest = fields.Float(
        string=u'Valor FCP', compute='_compute_price',
        digits=dp.get_precision('Discount'), )
    icms_uf_dest = fields.Float(
        u'ICMS Destino', compute='_compute_price',
        digits=dp.get_precision('Discount'))
    icms_uf_remet = fields.Float(
        u'ICMS Remetente', compute='_compute_price',
        digits=dp.get_precision('Discount'))

    # =========================================================================
    # ICMS Simples Nacional
    # =========================================================================
    tax_simples_id = fields.Many2one(
        'account.tax', help=u"Alíquota utilizada no Simples Nacional",
        string=u"Alíquota Simples", domain=[('domain', '=', 'simples')])
    icms_csosn_simples = fields.Selection(CSOSN_SIMPLES, string="CSOSN ICMS")
    icms_aliquota_credito = fields.Float(u"% Cŕedito ICMS")
    icms_valor_credito = fields.Float(
        u"Valor de Crédito", compute='_compute_price', store=True)
    icms_st_aliquota_deducao = fields.Float(
        string=u"% ICMS Próprio",
        help="Alíquota interna ou interestadual aplicada \
         sobre o valor da operação para deduzir do ICMS ST - Para empresas \
         do Simples Nacional ou usado em casos onde existe apenas ST sem ICMS")

    # =========================================================================
    # ISSQN
    # =========================================================================
    issqn_rule_id = fields.Many2one(
        'account.fiscal.position.tax.rule', 'Regra')
    tax_issqn_id = fields.Many2one('account.tax', string=u"Alíquota ISSQN",
                                   domain=[('domain', '=', 'issqn')])
    issqn_tipo = fields.Selection([('N', 'Normal'),
                                   ('R', 'Retida'),
                                   ('S', 'Substituta'),
                                   ('I', 'Isenta')],
                                  string='Tipo do ISSQN',
                                  required=True, default='N')
    service_type_id = fields.Many2one(
        'br_account.service.type', u'Tipo de Serviço')
    issqn_base_calculo = fields.Float(
        'Base ISSQN', digits=dp.get_precision('Account'),
        compute='_compute_price', store=True)
    issqn_aliquota = fields.Float(
        'Perc ISSQN', required=True, digits=dp.get_precision('Discount'),
        default=0.00)
    issqn_valor = fields.Float(
        'Valor ISSQN', required=True, digits=dp.get_precision('Account'),
        default=0.00, compute='_compute_price', store=True)

    # =========================================================================
    # IPI
    # =========================================================================
    ipi_rule_id = fields.Many2one('account.fiscal.position.tax.rule', 'Regra')
    tax_ipi_id = fields.Many2one('account.tax', string=u"Alíquota IPI",
                                 domain=[('domain', '=', 'ipi')])
    ipi_tipo = fields.Selection(
        [('percent', 'Percentual')],
        'Tipo do IPI', required=True, default='percent')
    ipi_base_calculo = fields.Float(
        'Base IPI', required=True, digits=dp.get_precision('Account'),
        default=0.00, compute='_compute_price', store=True,)
    ipi_reducao_bc = fields.Float(
        u'% Redução Base', required=True, digits=dp.get_precision('Account'),
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
    pis_rule_id = fields.Many2one('account.fiscal.position.tax.rule', 'Regra')
    tax_pis_id = fields.Many2one('account.tax', string=u"Alíquota PIS",
                                 domain=[('domain', '=', 'pis')])
    pis_cst = fields.Selection(CST_PIS_COFINS, 'CST PIS')
    pis_tipo = fields.Selection([('percent', 'Percentual')],
                                string='Tipo do PIS', required=True,
                                default='percent')
    pis_base_calculo = fields.Float(
        'Base PIS', required=True, compute='_compute_price', store=True,
        digits=dp.get_precision('Account'), default=0.00)
    pis_valor = fields.Float(
        'Valor PIS', required=True, digits=dp.get_precision('Account'),
        default=0.00, compute='_compute_price', store=True)
    pis_aliquota = fields.Float(
        'Perc PIS', required=True, digits=dp.get_precision('Discount'),
        default=0.00)

    # =========================================================================
    # COFINS
    # =========================================================================
    cofins_rule_id = fields.Many2one(
        'account.fiscal.position.tax.rule', 'Regra')
    tax_cofins_id = fields.Many2one('account.tax', string=u"Alíquota COFINS",
                                    domain=[('domain', '=', 'cofins')])
    cofins_cst = fields.Selection(CST_PIS_COFINS, 'CST PIS')
    cofins_tipo = fields.Selection([('percent', 'Percentual')],
                                   string='Tipo do COFINS', required=True,
                                   default='percent')
    cofins_base_calculo = fields.Float(
        'Base COFINS', compute='_compute_price', store=True,
        digits=dp.get_precision('Account'))
    cofins_valor = fields.Float(
        'Valor COFINS', digits=dp.get_precision('Account'),
        compute='_compute_price', store=True)
    cofins_aliquota = fields.Float(
        'Perc COFINS', digits=dp.get_precision('Discount'))

    # =========================================================================
    # Imposto de importação
    # =========================================================================
    ii_rule_id = fields.Many2one('account.fiscal.position.tax.rule', 'Regra')
    tax_ii_id = fields.Many2one('account.tax', string=u"Alíquota II",
                                domain=[('domain', '=', 'ii')])
    ii_base_calculo = fields.Float(
        'Base II', required=True, digits=dp.get_precision('Account'),
        default=0.00, compute='_compute_price', store=True)
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
        'Desp. Aduaneiras', required=True,
        digits=dp.get_precision('Account'), default=0.00)
    import_declaration_ids = fields.One2many(
        'br_account.import.declaration',
        'invoice_line_id', u'Declaração de Importação')

    # =========================================================================
    # Impostos de serviço - CSLL
    # =========================================================================
    csll_rule_id = fields.Many2one('account.fiscal.position.tax.rule', 'Regra')
    tax_csll_id = fields.Many2one('account.tax', string=u"Alíquota CSLL",
                                  domain=[('domain', '=', 'csll')])
    csll_base_calculo = fields.Float(
        'Base CSLL', required=True, digits=dp.get_precision('Account'),
        default=0.00, compute='_compute_price', store=True)
    csll_valor = fields.Float(
        'Valor CSLL', required=True, digits=dp.get_precision('Account'),
        default=0.00, compute='_compute_price', store=True)
    csll_aliquota = fields.Float(
        'Perc CSLL', required=True, digits=dp.get_precision('Account'),
        default=0.00)

    # =========================================================================
    # Impostos de serviço - IRRF
    # =========================================================================
    irrf_rule_id = fields.Many2one('account.fiscal.position.tax.rule', 'Regra')
    tax_irrf_id = fields.Many2one('account.tax', string=u"Alíquota IRRF",
                                  domain=[('domain', '=', 'irrf')])
    irrf_base_calculo = fields.Float(
        'Base IRRF', required=True, digits=dp.get_precision('Account'),
        default=0.00, compute='_compute_price', store=True)
    irrf_valor = fields.Float(
        'Valor IRFF', required=True, digits=dp.get_precision('Account'),
        default=0.00, compute='_compute_price', store=True)
    irrf_aliquota = fields.Float(
        'Perc IRRF', required=True, digits=dp.get_precision('Account'),
        default=0.00)

    # =========================================================================
    # Impostos de serviço - INSS
    # =========================================================================
    inss_rule_id = fields.Many2one('account.fiscal.position.tax.rule', 'Regra')
    tax_inss_id = fields.Many2one('account.tax', string=u"Alíquota IRRF",
                                  domain=[('domain', '=', 'inss')])
    inss_base_calculo = fields.Float(
        'Base INSS', required=True, digits=dp.get_precision('Account'),
        default=0.00, compute='_compute_price', store=True)
    inss_valor = fields.Float(
        'Valor INSS', required=True, digits=dp.get_precision('Account'),
        default=0.00, compute='_compute_price', store=True)
    inss_aliquota = fields.Float(
        'Perc INSS', required=True, digits=dp.get_precision('Account'),
        default=0.00)

    informacao_adicional = fields.Text(string="Informações Adicionais")

    def _update_tax_from_ncm(self):
        if self.product_id:
            ncm = self.product_id.fiscal_classification_id
            self.update({
                'icms_st_aliquota_mva': ncm.icms_st_aliquota_mva,
                'icms_st_aliquota_reducao_base':
                ncm.icms_st_aliquota_reducao_base,
                'ipi_cst': ncm.ipi_cst,
                'ipi_reducao_bc': ncm.ipi_reducao_bc,
                'tax_icms_st_id': ncm.tax_icms_st_id.id,
                'tax_ipi_id': ncm.tax_ipi_id.id,
            })

    def _set_taxes(self):
        super(AccountInvoiceLine, self)._set_taxes()
        self._update_tax_from_ncm()
        fpos = self.invoice_id.fiscal_position_id
        if fpos:
            vals = fpos.map_tax_extra_values(
                self.company_id, self.product_id, self.invoice_id.partner_id)

            for key, value in vals.iteritems():
                if value and key in self._fields:
                    self.update({key: value})

        self.invoice_line_tax_ids = self.tax_icms_id | self.tax_icms_st_id | \
            self.tax_icms_inter_id | self.tax_icms_intra_id | \
            self.tax_icms_fcp_id | self.tax_simples_id | self.tax_ipi_id | \
            self.tax_pis_id | self.tax_cofins_id | self.tax_issqn_id | \
            self.tax_ii_id | self.tax_csll_id | self.tax_irrf_id | \
            self.tax_inss_id

    def _set_extimated_taxes(self, price):
        service = self.product_id.service_type_id
        ncm = self.product_id.fiscal_classification_id

        if self.product_type == 'service':
            self.tributos_estimados_federais = \
                price * (service.federal_nacional / 100)
            self.tributos_estimados_estaduais = \
                price * (service.estadual_imposto / 100)
            self.tributos_estimados_municipais = \
                price * (service.municipal_imposto / 100)
        else:
            federal = ncm.federal_nacional if self.icms_origem in \
                ('1', '2', '3', '8') else ncm.federal_importado

            self.tributos_estimados_federais = price * (federal / 100)
            self.tributos_estimados_estaduais = \
                price * (ncm.estadual_imposto / 100)
            self.tributos_estimados_municipais = \
                price * (ncm.municipal_imposto / 100)

        self.tributos_estimados = self.tributos_estimados_federais + \
            self.tributos_estimados_estaduais + \
            self.tributos_estimados_municipais

    @api.onchange('price_subtotal')
    def _br_account_onchange_quantity(self):
        self._set_extimated_taxes(self.price_subtotal)

    @api.onchange('product_id')
    def _br_account_onchange_product_id(self):
        self.product_type = self.product_id.fiscal_type
        self.icms_origem = self.product_id.origin
        ncm = self.product_id.fiscal_classification_id
        service = self.product_id.service_type_id
        self.fiscal_classification_id = ncm.id
        self.service_type_id = service.id

        self._set_extimated_taxes(self.product_id.lst_price)

    def _update_invoice_line_ids(self):
        other_taxes = self.invoice_line_tax_ids.filtered(
            lambda x: not x.domain)
        self.invoice_line_tax_ids = other_taxes | self.tax_icms_id | \
            self.tax_icms_st_id | self.tax_icms_inter_id | \
            self.tax_icms_intra_id | self.tax_icms_fcp_id | \
            self.tax_simples_id | self.tax_ipi_id | self.tax_pis_id | \
            self.tax_cofins_id | self.tax_issqn_id | self.tax_ii_id | \
            self.tax_csll_id | self.tax_irrf_id | self.tax_inss_id

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

    @api.onchange('tax_icms_inter_id')
    def _onchange_tax_icms_inter_id(self):
        self._update_invoice_line_ids()

    @api.onchange('tax_icms_intra_id')
    def _onchange_tax_icms_intra_id(self):
        self._update_invoice_line_ids()

    @api.onchange('tax_icms_fcp_id')
    def _onchange_tax_icms_fcp_id(self):
        self._update_invoice_line_ids()

    @api.onchange('tax_simples_id')
    def _onchange_tax_simples_id(self):
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

    @api.onchange('tax_issqn_id')
    def _onchange_tax_issqn_id(self):
        if self.tax_issqn_id:
            self.issqn_aliquota = self.tax_issqn_id.amount
        self._update_invoice_line_ids()

    @api.onchange('tax_csll_id')
    def _onchange_tax_csll_id(self):
        if self.tax_csll_id:
            self.csll_aliquota = self.tax_csll_id.amount
        self._update_invoice_line_ids()

    @api.onchange('tax_irrf_id')
    def _onchange_tax_irrf_id(self):
        if self.tax_irrf_id:
            self.irrf_aliquota = self.tax_irrf_id.amount
        self._update_invoice_line_ids()

    @api.onchange('tax_inss_id')
    def _onchange_tax_inss_id(self):
        if self.tax_inss_id:
            self.inss_aliquota = self.tax_inss_id.amount
        self._update_invoice_line_ids()
