# -*- coding: utf-8 -*-
# © 2009 Renato Lima - Akretion
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models
from odoo.addons import decimal_precision as dp
from .product import PRODUCT_ORIGIN


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.one
    @api.depends('invoice_line_ids.price_subtotal', 'tax_line_ids.amount',
                 'currency_id', 'company_id')
    def _compute_amount(self):
        super(AccountInvoice, self)._compute_amount()
        lines = self.invoice_line_ids
        self.icms_base = sum(l.icms_manual for l in lines)
        self.icms_base_other = sum(l.icms_base_other for l in lines)
        self.icms_value = sum(l.icms_value for l in lines)
        self.icms_st_base = sum(l.icms_st_base for l in lines)
        self.icms_st_value = sum(l.icms_st_value for l in lines)
        self.issqn_base = sum(l.issqn_base for l in lines)
        self.issqn_value = sum(l.issqn_value for l in lines)
        self.ipi_base = sum(l.ipi_base for l in lines)
        self.ipi_base_other = sum(l.ipi_base_other for l in lines)
        self.ipi_value = sum(l.ipi_value for l in lines)
        self.pis_base = sum(l.pis_base for l in lines)
        self.pis_value = sum(l.pis_value for l in lines)
        self.cofins_base = sum(l.cofins_base for l in lines)
        self.cofins_value = sum(l.cofins_value for l in lines)
        self.ii_value = sum(l.ii_value for l in lines)
        self.amount_gross = sum(l.price_gross for l in lines)
        self.amount_discount = sum(l.discount_value for l in lines)
        self.amount_insurance = sum(l.insurance_value for l in lines)
        self.amount_costs = sum(l.other_costs_value for l in lines)
        self.amount_estimated_tax = sum(l.estimated_taxes for l in lines)

    @api.one
    @api.depends('move_id.line_ids')
    def _compute_receivables(self):
        receivable_lines = []
        for line in self.move_id.line_ids:
            if line.account_id.user_type_id.type == "receivable":
                receivable_lines.append(line.id)
        self.receivable_move_line_ids = self.env['account.move.line'].browse(
            list(set(receivable_lines)))

    @api.one
    @api.depends('move_id.line_ids')
    def _compute_payables(self):
        receivable_lines = []
        for line in self.move_id.line_ids:
            if line.account_id.user_type_id.type == "payable":
                receivable_lines.append(line.id)
        self.receivable_move_line_ids = self.env['account.move.line'].browse(
            list(set(receivable_lines)))

    @api.model
    def _default_fiscal_document(self):
        company = self.env['res.company'].browse(self.env.user.company_id.id)
        return company.fiscal_document_for_product_id

    @api.model
    def _default_fiscal_document_serie(self):
        company = self.env['res.company'].browse(self.env.user.company_id.id)
        return company.document_serie_id.id

    receivable_move_line_ids = fields.Many2many(
        'account.move.line', string='Receivable Move Lines',
        compute='_compute_receivables')

    payable_move_line_ids = fields.Many2many(
        'account.move.line', string='Payable Move Lines',
        compute='_compute_payables')

    issuer = fields.Selection(
        [('0', 'Terceiros'), ('1', u'Emissão própria')], 'Emitente',
        default='0', readonly=True, states={'draft': [('readonly', False)]})
    vendor_number = fields.Char(
        'Número NF Entrada', size=18, readonly=True,
        states={'draft': [('readonly', False)]},
        help=u"Número da Nota Fiscal do Fornecedor")
    vendor_serie = fields.Char(
        'Série NF Entrada', size=12, readonly=True,
        states={'draft': [('readonly', False)]},
        help=u"Série do número da Nota Fiscal do Fornecedor")
    document_serie_id = fields.Many2one(
        'br_account.document.serie', string=u'Série',
        domain="[('fiscal_document_id', '=', fiscal_document_id),\
        ('company_id','=',company_id)]", readonly=True,
        states={'draft': [('readonly', False)]},
        default=_default_fiscal_document_serie)
    fiscal_document_id = fields.Many2one(
        'br_account.fiscal.document', string='Documento', readonly=True,
        states={'draft': [('readonly', False)]},
        default=_default_fiscal_document)
    is_eletronic = fields.Boolean(
        related='fiscal_document_id.electronic', type='boolean',
        store=True, string='Electronic')
    fiscal_comment = fields.Text(u'Observação Fiscal')

    amount_gross = fields.Float(
        string='Vlr. Bruto',
        store=True,
        digits=dp.get_precision('Account'),
        compute='_compute_amount',
        readonly=True)
    amount_discount = fields.Float(
        string='Desconto',
        store=True,
        digits=dp.get_precision('Account'),
        compute='_compute_amount')
    icms_base = fields.Float(
        string='Base ICMS',
        store=True,
        digits=dp.get_precision('Account'),
        compute='_compute_amount')
    icms_base_other = fields.Float(
        string='Base ICMS Outras',
        store=True,
        digits=dp.get_precision('Account'),
        compute='_compute_amount',
        readonly=True)
    icms_value = fields.Float(
        string='Valor ICMS', digits=dp.get_precision('Account'),
        compute='_compute_amount', store=True)
    icms_st_base = fields.Float(
        string='Base ICMS ST',
        store=True,
        digits=dp.get_precision('Account'),
        compute='_compute_amount')
    icms_st_value = fields.Float(
        string='Valor ICMS ST',
        store=True,
        digits=dp.get_precision('Account'),
        compute='_compute_amount')
    issqn_base = fields.Float(
        string='Base ISSQN', store=True,
        digits=dp.get_precision('Account'), compute='_compute_amount')
    issqn_value = fields.Float(
        string='Valor ISSQN', store=True,
        digits=dp.get_precision('Account'), compute='_compute_amount')
    ipi_base = fields.Float(
        string='Base IPI', store=True, digits=dp.get_precision('Account'),
        compute='_compute_amount')
    ipi_base_other = fields.Float(
        string="Base IPI Outras", store=True,
        digits=dp.get_precision('Account'), compute='_compute_amount')
    ipi_value = fields.Float(
        string='Valor IPI', store=True,
        digits=dp.get_precision('Account'), compute='_compute_amount')
    pis_base = fields.Float(
        string='Base PIS', store=True,
        digits=dp.get_precision('Account'), compute='_compute_amount')
    pis_value = fields.Float(
        string='Valor PIS', store=True,
        digits=dp.get_precision('Account'), compute='_compute_amount')
    cofins_base = fields.Float(
        string='Base COFINS', store=True,
        digits=dp.get_precision('Account'), compute='_compute_amount')
    cofins_value = fields.Float(
        string='Valor COFINS', store=True,
        digits=dp.get_precision('Account'), compute='_compute_amount',
        readonly=True)
    ii_value = fields.Float(
        string='Valor II', store=True,
        digits=dp.get_precision('Account'), compute='_compute_amount',
        readonly=True)
    amount_insurance = fields.Float(
        string='Valor do Seguro', store=True,
        digits=dp.get_precision('Account'), compute='_compute_amount')
    amount_costs = fields.Float(
        string='Outros Custos', store=True,
        digits=dp.get_precision('Account'), compute='_compute_amount')
    amount_estimated_tax = fields.Float(
        string='Total de Tributos',
        store=True,
        digits=dp.get_precision('Account'),
        compute='_compute_amount')


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    @api.one
    @api.depends('price_unit', 'discount', 'invoice_line_tax_ids', 'quantity',
                 'product_id', 'invoice_id.partner_id',
                 'invoice_id.currency_id', 'invoice_id.company_id')
    def _compute_price(self):
        super(AccountInvoiceLine, self)._compute_price()
        self.price_gross = self.quantity * self.price_unit
        self.discount_value = self.price_gross * (self.discount / 100)

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
        string='Total de Tributos', requeried=True, default=0.00,
        digits=dp.get_precision('Account'))

    tax_icms_id = fields.Many2one('account.tax', string="ICMS",
                                  domain=[('domain', '=', 'icms')])

    icms_manual = fields.Boolean('ICMS Manual?', default=False)
    icms_origin = fields.Selection(PRODUCT_ORIGIN, 'Origem', default='0')
    icms_base_type = fields.Selection(
        [('0', 'Margem Valor Agregado (%)'), ('1', 'Pauta (valor)'),
         ('2', 'Preço Tabelado Máximo (valor)'),
         ('3', 'Valor da Operação')],
        'Tipo Base ICMS', required=True, default='0')
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
        'Perc Redução de Base ICMS', digits=dp.get_precision('Discount'),
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
    icms_cst = fields.Char('CST ICMS', size=10)
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
    issqn_manual = fields.Boolean('ISSQN Manual?', default=False)
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
    ipi_manual = fields.Boolean('IPI Manual?', default=False)
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
    ipi_cst = fields.Char('CST IPI', size=10)
    tax_pis_id = fields.Many2one('account.tax', string="PIS",
                                 domain=[('domain', '=', 'pis')])
    pis_manual = fields.Boolean('PIS Manual?', default=False)
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
    cofins_manual = fields.Boolean('COFINS Manual?', default=False)
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
