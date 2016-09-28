# -*- coding: utf-8 -*-
# © 2009 Renato Lima - Akretion
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import api, fields, models
from odoo.addons import decimal_precision as dp
from .product import PRODUCT_ORIGIN
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
        super(AccountInvoiceLine, self)._compute_price()
        self.price_gross = self.quantity * self.price_unit
        self.discount_value = self.price_gross * (self.discount / 100)

    @api.onchange('quantity', 'price_unit', 'discount',
                  'insurance_value', 'other_costs_value')
    def _recompute_tax_values(self):
        if self.calculate_tax:
            base_icms = base = self.quantity * self.price_unit
            self.ipi_base = base
            self.ipi_value = base * self.ipi_percent
            self.pis_base = base
            self.pis_value = base * self.cofins_percent
            self.cofins_base = base
            self.cofins_value = base * self.cofins_percent
            self.issqn_base = base
            self.issqn_value = base * self.issqn_percent
            self.ii_base = base
            self.ii_value = base * self.ii_percent

            if self.include_ipi_base:
                base_icms += self.ipi_base * self.ipi_percent
            base_icms += self.insurance_value + self.other_costs_value
            base_icms -= self.discount_value

            self.icms_base = base_icms * (1 - self.icms_percent_reduction / 100)
            self.icms_value = self.icms_base * (self.icms_percent / 100)

            self.icms_st_base = base * self.icms_st_mva * \
                (1 - self.icms_st_percent_reduction / 100)

            self.icms_st_value = self.icms_value - \
                (self.icms_st_base * self.icms_st_percent)

    calculate_tax = fields.Boolean(string="Calcular Imposto?", default=True)

    company_fiscal_type = fields.Selection(
        COMPANY_FISCAL_TYPE,
        default=_default_company_fiscal_type,
        string="Regime Tributário")

    cfop_id = fields.Many2one('br_account.cfop', 'CFOP')
    fiscal_classification_id = fields.Many2one(
        'product.fiscal.classification', 'Classificação Fiscal')
    product_type = fields.Selection(
        [('product', 'Produto'), ('service', 'Serviço')],
        string='Tipo do Produto', required=True, default='product')
    discount_value = fields.Float(
        string='Vlr. desconto', store=True, compute='_compute_price',
        digits=dp.get_precision('Account'))
    price_gross = fields.Float(
        string='Vlr. Bruto', store=True, compute='_compute_price',
        digits=dp.get_precision('Account'))
    estimated_taxes = fields.Float(
        string='Total Estimado de Tributos', requeried=True, default=0.00,
        digits=dp.get_precision('Account'))

    tax_icms_id = fields.Many2one('account.tax', string="ICMS",
                                  domain=[('domain', '=', 'icms')])

    icms_origin = fields.Selection(PRODUCT_ORIGIN, 'Origem', default='0')
    icms_base_type = fields.Selection(
        [('0', 'Margem Valor Agregado (%)'), ('1', 'Pauta (valor)'),
         ('2', 'Preço Tabelado Máximo (valor)'),
         ('3', 'Valor da Operação')],
        'Tipo Base ICMS', required=True, default='0')
    include_ipi_base = fields.Boolean(
        string="Incl. Vlr Ipi?",
        help="Se marcado o valor do IPI inclui a base de cálculo")
    icms_base = fields.Float('Base ICMS', required=True,
                             digits=dp.get_precision('Account'), default=0.00)
    icms_base_other = fields.Float(
        'Base ICMS Outras', required=True,
        digits=dp.get_precision('Account'), default=0.00)
    icms_value = fields.Float(
        'Valor ICMS', required=True,
        digits=dp.get_precision('Account'), default=0.00)
    icms_percent = fields.Float(
        'Perc ICMS', digits=dp.get_precision('Discount'), default=0.00)
    icms_percent_reduction = fields.Float(
        '% Red. Base ICMS', digits=dp.get_precision('Discount'),
        default=0.00)
    icms_st_base_type = fields.Selection(
        [('0', 'Preço tabelado ou máximo  sugerido'),
         ('1', 'Lista Negativa (valor)'),
         ('2', 'Lista Positiva (valor)'), ('3', 'Lista Neutra (valor)'),
         ('4', 'Margem Valor Agregado (%)'), ('5', 'Pauta (valor)')],
        'Tipo Base ICMS ST', required=True, default='4')
    icms_st_value = fields.Float(
        'Valor ICMS ST', required=True,
        digits=dp.get_precision('Account'), default=0.00)
    icms_st_base = fields.Float(
        'Base ICMS ST', required=True,
        digits=dp.get_precision('Account'), default=0.00)
    icms_st_percent = fields.Float(
        '% ICMS ST', digits=dp.get_precision('Discount'),
        default=0.00)
    icms_st_percent_reduction = fields.Float(
        '% Red. Base ST',
        digits=dp.get_precision('Discount'), default=0.00)
    icms_st_mva = fields.Float(
        'MVA Ajustado ST',
        digits=dp.get_precision('Discount'), default=0.00)
    icms_st_base_other = fields.Float(
        'Base ICMS ST Outras', required=True,
        digits=dp.get_precision('Account'), default=0.00)

    @api.multi
    @api.depends('icms_cst_normal', 'icms_csosn_simples',
                 'company_fiscal_type')
    def _compute_cst_icms(self):
        for item in self:
            item.icms_cst = item.icms_cst_normal \
                if item.company_fiscal_type == '3' else item.icms_csosn_simples

    icms_cst = fields.Char('CST ICMS', size=10,
                           store=True, compute='_compute_cst_icms')
    icms_cst_normal = fields.Selection([
        ('00', '00 - Tributada Integralmente'),
        ('10', '10 - Tributada e com cobrança do ICMS por substituição \
         tributária'),
        ('20', '20 - Com redução de base de cálculo'),
        ('30', '30 - Isenta ou não tributada e com cobrança do ICMS por \
         substituição tributária'),
        ('40', '40 - Isenta'),
        ('41', '41 - Não tributada'),
        ('50', '50 - Suspensão'),
        ('51', '51 - Diferimento'),
        ('60', '60 - ICMS cobrado anteriormente por substituição tributária'),
        ('70', '70 - Com redução de base de cálculo e cobrança do ICMS por \
         substituição tributária'),
        ('90', '90 - Outras')], string="CST ICMS")

    icms_csosn_simples = fields.Selection([
        ('101', '101 - Tributada pelo Simples Nacional com permissão de \
         crédito'),
        ('102', '102 - Tributada pelo Simples Nacional sem permissão de \
         crédito'),
        ('103', '103 -Isenção do ICMS no Simples Nacional para faixa de \
         receita bruta'),
        ('201', '201 - Tributada pelo Simples Nacional com permissão de \
         crédito e com cobrança do ICMS por substituição tributária'),
        ('202', '202 - Tributada pelo Simples Nacional sem permissão de \
         crédito e com cobrança do ICMS por substituição tributária'),
        ('203', '203 - Isenção do ICMS no Simples Nacional para faixa de \
         receita bruta e com cobrança do ICMS por substituição tributária'),
        ('300', '300 - Imune'),
        ('400', '400 - Não tributada pelo Simples Nacional'),
        ('500', '500 - ICMS cobrado anteriormente por substituição tributária \
         (substituído) ou por antecipação'),
        ('900', '900 - Outros')], string="CSOSN ICMS")

    icms_percent_credit = fields.Float(u"% Cŕedito ICMS")
    icms_value_credit = fields.Float(u"Valor de Crédito")
    origin_product = fields.Selection(
        [('0', '0 - Nacional'),
         ('1', '1 - Estrangeira - Importação direta'),
         ('2', '2 - Estrangeira - Adquirida no mercado interno'),
         ('3', '3 - Nacional, mercadoria ou bem com Conteúdo de Importação \
superior a 40% \e inferior ou igual a 70%'),
         ('4', '4 - Nacional, cuja produção tenha sido feita em conformidade \
com os processos produtivos básicos de que tratam as \
legislações citadas nos Ajustes'),
         ('5', '5 - Nacional, mercadoria ou bem com Conteúdo de Importação \
inferior ou igual a 40%'),
         ('6', '6 - Estrangeira - Importação direta, sem similar nacional, \
constante em lista da CAMEX e gás natural'),
         ('7', '7 - Estrangeira - Adquirida no mercado interno, sem similar \
nacional, constante lista CAMEX e gás natural'),
         ('8', '8 - Nacional, mercadoria ou bem com Conteúdo de Importação \
superior a 70%')],
        u'Origem da mercadoria')

    tax_issqn_id = fields.Many2one('account.tax', string="ISSQN",
                                   domain=[('domain', '=', 'issqn')])
    issqn_type = fields.Selection(
        [('N', 'Normal'), ('R', 'Retida'),
         ('S', 'Substituta'), ('I', 'Isenta')], 'Tipo do ISSQN',
        required=True, default='N')
    service_type_id = fields.Many2one(
        'br_account.service.type', 'Tipo de Serviço')
    issqn_base = fields.Float(
        'Base ISSQN', required=True, digits=dp.get_precision('Account'),
        default=0.00)
    issqn_percent = fields.Float(
        'Perc ISSQN', required=True, digits=dp.get_precision('Discount'),
        default=0.00)
    issqn_value = fields.Float(
        'Valor ISSQN', required=True, digits=dp.get_precision('Account'),
        default=0.00)
    tax_ipi_id = fields.Many2one('account.tax', string="IPI",
                                 domain=[('domain', '=', 'ipi')])
    ipi_type = fields.Selection(
        [('percent', 'Percentual'), ('quantity', 'Em Valor')],
        'Tipo do IPI', required=True, default='percent')
    ipi_base = fields.Float(
        'Base IPI', required=True, digits=dp.get_precision('Account'),
        default=0.00)
    ipi_base_other = fields.Float(
        'Base IPI Outras', required=True, digits=dp.get_precision('Account'),
        default=0.00)
    ipi_value = fields.Float(
        'Valor IPI', required=True, digits=dp.get_precision('Account'),
        default=0.00)
    ipi_percent = fields.Float(
        'Perc IPI', required=True, digits=dp.get_precision('Discount'),
        default=0.00)
    ipi_cst = fields.Selection([
        ('00', '00 - Entrada com Recuperação de Crédito'),
        ('01', '01 - Entrada Tributável com Alíquota Zero'),
        ('02', '02 - Entrada Isenta'),
        ('03', '03 - Entrada Não-Tributada'),
        ('04', '04 - Entrada Imune'),
        ('05', '05 - Entrada com Suspensão'),
        ('49', '49 - Outras Entradas'),
        ('50', '50 - Saída Tributada'),
        ('51', '51 - Saída Tributável com Alíquota Zero'),
        ('52', '52 - Saída Isenta'),
        ('53', '52 - Saída Não-Tributada'),
        ('54', '54 - Saída Imune'),
        ('55', '55 - Saída com Suspensão'),
        ('99', '99 - Outras Saídas')], string='CST IPI')
    tax_pis_id = fields.Many2one('account.tax', string="PIS",
                                 domain=[('domain', '=', 'pis')])
    pis_type = fields.Selection(
        [('percent', 'Percentual'), ('quantity', 'Em Valor')],
        'Tipo do PIS', required=True, default='percent')
    pis_base = fields.Float('Base PIS', required=True,
                            digits=dp.get_precision('Account'), default=0.00)
    pis_base_other = fields.Float(
        'Base PIS Outras', required=True, digits=dp.get_precision('Account'),
        default=0.00)
    pis_value = fields.Float(
        'Valor PIS', required=True, digits=dp.get_precision('Account'),
        default=0.00)
    pis_percent = fields.Float(
        'Perc PIS', required=True, digits=dp.get_precision('Discount'),
        default=0.00)
    pis_cst = fields.Char('CST PIS', size=10)
    pis_st_type = fields.Selection(
        [('percent', 'Percentual'), ('quantity', 'Em Valor')],
        'Tipo do PIS ST', required=True, default='percent')
    pis_st_base = fields.Float(
        'Base PIS ST', required=True, digits=dp.get_precision('Account'),
        default=0.00)
    pis_st_percent = fields.Float(
        'Perc PIS ST', required=True, digits=dp.get_precision('Account'),
        default=0.00)
    pis_st_value = fields.Float(
        'Valor PIS ST', required=True, digits=dp.get_precision('Account'),
        default=0.00)
    tax_cofins_id = fields.Many2one('account.tax', string="COFINS",
                                    domain=[('domain', '=', 'cofins')])
    cofins_type = fields.Selection(
        [('percent', 'Percentual'), ('quantity', 'Em Valor')],
        'Tipo do COFINS', required=True, default='percent')
    cofins_base = fields.Float(
        'Base COFINS',
        required=True,
        digits=dp.get_precision('Account'),
        default=0.00)
    cofins_base_other = fields.Float(
        'Base COFINS Outras', required=True,
        digits=dp.get_precision('Account'), default=0.00)
    cofins_value = fields.Float(
        'Valor COFINS', required=True, digits=dp.get_precision('Account'),
        default=0.00)
    cofins_percent = fields.Float(
        'Perc COFINS', required=True, digits=dp.get_precision('Discount'),
        default=0.00)
    cofins_cst = fields.Char('CST PIS')
    cofins_st_type = fields.Selection(
        [('percent', 'Percentual'), ('quantity', 'Em Valor')],
        'Tipo do COFINS ST', required=True, default='percent')
    cofins_st_base = fields.Float(
        'Base COFINS ST', required=True, digits=dp.get_precision('Account'),
        default=0.00)
    cofins_st_percent = fields.Float(
        'Perc COFINS ST', required=True, digits=dp.get_precision('Discount'),
        default=0.00)
    cofins_st_value = fields.Float(
        'Valor COFINS ST', required=True, digits=dp.get_precision('Account'),
        default=0.00)
    tax_ii_id = fields.Many2one('account.tax', string="II",
                                domain=[('domain', '=', 'ii')])
    ii_base = fields.Float(
        'Base II', required=True, digits=dp.get_precision('Account'),
        default=0.00)
    ii_percent = fields.Float(
        '% II', required=True, digits=dp.get_precision('Account'),
        default=0.00)
    ii_value = fields.Float(
        'Valor II', required=True, digits=dp.get_precision('Account'),
        default=0.00)
    ii_iof = fields.Float(
        'Valor IOF', required=True, digits=dp.get_precision('Account'),
        default=0.00)
    ii_customhouse_charges = fields.Float(
        'Depesas Atuaneiras', required=True,
        digits=dp.get_precision('Account'), default=0.00)
    insurance_value = fields.Float(
        'Valor do Seguro', digits=dp.get_precision('Account'), default=0.00)
    other_costs_value = fields.Float(
        'Outros Custos', digits=dp.get_precision('Account'), default=0.00)
    fiscal_comment = fields.Text(u'Observação Fiscal')

    def _set_taxes(self):
        super(AccountInvoiceLine, self)._set_taxes()
        self.tax_icms_id = self.invoice_line_tax_ids.filtered(
            lambda r: r.domain == 'icms').id
        self.tax_issqn_id = self.invoice_line_tax_ids.filtered(
            lambda r: r.domain == 'issqn').id
        self.tax_ipi_id = self.invoice_line_tax_ids.filtered(
            lambda r: r.domain == 'ipi').id
        self.tax_cofins_id = self.invoice_line_tax_ids.filtered(
            lambda r: r.domain == 'cofins').id
        self.tax_pis_id = self.invoice_line_tax_ids.filtered(
            lambda r: r.domain == 'pis').id
        self.tax_ii_id = self.invoice_line_tax_ids.filtered(
            lambda r: r.domain == 'ii').id

    @api.onchange('product_id')
    def _br_account_onchange_product_id(self):
        self.service_type_id = self.product_id.service_type_id.id
        self.product_type = self.product_id.fiscal_type
        self.fiscal_classification_id = \
            self.product_id.fiscal_classification_id.id

    @api.onchange('tax_icms_id')
    def _onchange_tax_icms_id(self):
        if self.tax_icms_id:
            self.icms_percent = self.tax_icms_id.amount
            self.icms_cst = self.tax_icms_id.cst

    @api.onchange('tax_pis_id')
    def _onchange_tax_pis_id(self):
        if self.tax_pis_id:
            self.pis_percent = self.tax_pis_id.amount
            self.pis_cst = self.tax_ipi_id.cst

    @api.onchange('tax_cofins_id')
    def _onchange_tax_cofins_id(self):
        if self.tax_cofins_id:
            self.cofins_percent = self.tax_cofins_id.amount
            self.cofins_cst = self.tax_ipi_id.cst

    @api.onchange('tax_ipi_id')
    def _onchange_tax_ipi_id(self):
        if self.tax_ipi_id:
            self.ipi_percent = self.tax_ipi_id.amount
            self.ipi_cst = self.tax_ipi_id.cst

    @api.onchange('tax_ii_id')
    def _onchange_tax_ii_id(self):
        if self.tax_ii_id:
            self.ii_percent = self.tax_ii_id.amount
