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
    _name = 'account.invoice.line'
    _inherit = ['account.invoice.line', 'br.localization.filtering']

    @api.model
    def _default_company_fiscal_type(self):
        if self.invoice_id:
            return self.invoice_id.company_id.l10n_br_fiscal_type
        company = self.env['res.company'].browse(self.env.user.company_id.id)
        return company.l10n_br_fiscal_type

    def _prepare_tax_context(self):
        return {
            'incluir_ipi_base': self.l10n_br_incluir_ipi_base,
            'icms_st_aliquota_mva': self.l10n_br_icms_st_aliquota_mva,
            'icms_aliquota_reducao_base':
                self.l10n_br_icms_aliquota_reducao_base,
            'icms_st_aliquota_reducao_base':
                self.l10n_br_icms_st_aliquota_reducao_base,
            'icms_st_aliquota_deducao':
                self.l10n_br_icms_st_aliquota_deducao,
            'icms_st_base_calculo_manual':
                self.l10n_br_icms_st_base_calculo_manual,
            'ipi_reducao_bc': self.l10n_br_ipi_reducao_bc,
            'icms_base_calculo': self.l10n_br_icms_base_calculo,
            'icms_base_calculo_manual':
                self.l10n_br_icms_base_calculo_manual,
            'ipi_base_calculo': self.l10n_br_ipi_base_calculo,
            'ipi_base_calculo_manual':
                self.l10n_br_ipi_base_calculo_manual,
            'pis_base_calculo': self.l10n_br_pis_base_calculo,
            'pis_base_calculo_manual':
                self.l10n_br_pis_base_calculo_manual,
            'cofins_base_calculo': self.l10n_br_cofins_base_calculo,
            'cofins_base_calculo_manual':
                self.l10n_br_cofins_base_calculo_manual,
            'ii_base_calculo': self.l10n_br_ii_base_calculo,
            'issqn_base_calculo': self.l10n_br_issqn_base_calculo,
            'icms_aliquota_inter_part':
                self.l10n_br_icms_aliquota_inter_part,
            'issqn_deduction': self.l10n_br_issqn_deduction,
        }

    @api.one
    @api.depends('price_unit', 'discount', 'invoice_line_tax_ids', 'quantity',
                 'product_id', 'invoice_id.partner_id',
                 'invoice_id.currency_id', 'invoice_id.company_id',
                 'l10n_br_tax_icms_id', 'l10n_br_tax_icms_st_id',
                 'l10n_br_tax_icms_inter_id', 'l10n_br_tax_icms_intra_id',
                 'l10n_br_tax_icms_fcp_id', 'l10n_br_tax_ipi_id',
                 'l10n_br_tax_pis_id', 'l10n_br_tax_cofins_id',
                 'l10n_br_tax_ii_id', 'l10n_br_tax_issqn_id',
                 'l10n_br_tax_csll_id', 'l10n_br_tax_irrf_id',
                 'l10n_br_tax_inss_id', 'l10n_br_incluir_ipi_base',
                 'l10n_br_tem_difal', 'l10n_br_icms_aliquota_reducao_base',
                 'l10n_br_ipi_reducao_bc', 'l10n_br_icms_st_aliquota_mva',
                 'l10n_br_icms_st_aliquota_reducao_base',
                 'l10n_br_icms_aliquota_credito',
                 'l10n_br_icms_st_aliquota_deducao',
                 'l10n_br_icms_st_base_calculo_manual',
                 'l10n_br_icms_base_calculo_manual',
                 'l10n_br_ipi_base_calculo_manual',
                 'l10n_br_pis_base_calculo_manual',
                 'l10n_br_cofins_base_calculo_manual',
                 'l10n_br_icms_st_aliquota_deducao', 'l10n_br_ii_base_calculo',
                 'l10n_br_icms_aliquota_inter_part', 'l10n_br_issqn_deduction')
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
                 if x['id'] == self.l10n_br_tax_icms_id.id]) if taxes else []
        icmsst = (
            [x for x in taxes['taxes']
             if x['id'] == self.l10n_br_tax_icms_st_id.id]) if taxes else []
        icms_inter = (
            [x for x in taxes['taxes']
             if x['id'] == self.l10n_br_tax_icms_inter_id.id]) if taxes else []
        icms_intra = (
            [x for x in taxes['taxes']
             if x['id'] == self.l10n_br_tax_icms_intra_id.id]) if taxes else []
        icms_fcp = (
            [x for x in taxes['taxes']
             if x['id'] == self.l10n_br_tax_icms_fcp_id.id]) if taxes else []
        ipi = ([x for x in taxes['taxes']
                if x['id'] == self.l10n_br_tax_ipi_id.id]) if taxes else []
        pis = ([x for x in taxes['taxes']
                if x['id'] == self.l10n_br_tax_pis_id.id]) if taxes else []
        cofins = (
            [x for x in taxes['taxes']
             if x['id'] == self.l10n_br_tax_cofins_id.id]) if taxes else []
        issqn = ([x for x in taxes['taxes']
                  if x['id'] == self.l10n_br_tax_issqn_id.id]) if taxes else []
        ii = ([x for x in taxes['taxes']
               if x['id'] == self.l10n_br_tax_ii_id.id]) if taxes else []
        csll = ([x for x in taxes['taxes']
                 if x['id'] == self.l10n_br_tax_csll_id.id]) if taxes else []
        irrf = ([x for x in taxes['taxes']
                 if x['id'] == self.l10n_br_tax_irrf_id.id]) if taxes else []
        inss = ([x for x in taxes['taxes']
                 if x['id'] == self.l10n_br_tax_inss_id.id]) if taxes else []
        price_subtotal_signed = taxes['total_excluded'] if taxes else subtotal
        if self.invoice_id.currency_id and self.invoice_id.currency_id != \
                self.invoice_id.company_id.currency_id:
            price_subtotal_signed = self.invoice_id.currency_id.compute(
                price_subtotal_signed, self.invoice_id.company_id.currency_id)
        sign = self.invoice_id.type in ['in_refund', 'out_refund'] and -1 or 1

        if self.l10n_br_icms_aliquota_credito:
            # Calcular o valor da base_icms para o calculo de
            # credito de ICMS
            ctx = self._prepare_tax_context()
            valor_frete = ctx.get('valor_frete', 0.0)
            valor_seguro = ctx.get('valor_seguro', 0.0)
            outras_despesas = ctx.get('outras_despesas', 0.0)

            base_icms_credito = subtotal + valor_frete \
                + valor_seguro + outras_despesas
        else:
            base_icms_credito = 0.0

        price_subtotal_signed = price_subtotal_signed * sign
        self.update({
            'price_total': taxes['total_included'] if taxes else subtotal,
            'l10n_br_price_tax':
                taxes['total_included'] - taxes['total_excluded']
                if taxes else 0,
            'price_subtotal': taxes['total_excluded'] if taxes else subtotal,
            'price_subtotal_signed': price_subtotal_signed,
            'l10n_br_valor_bruto': self.quantity * self.price_unit,
            'l10n_br_valor_desconto': desconto,
            'l10n_br_icms_base_calculo': sum([x['base'] for x in icms]),
            'l10n_br_icms_valor': sum([x['amount'] for x in icms]),
            'l10n_br_icms_st_base_calculo': sum([x['base'] for x in icmsst]),
            'l10n_br_icms_st_valor': sum([x['amount'] for x in icmsst]),
            'l10n_br_icms_bc_uf_dest': sum([x['base'] for x in icms_inter]),
            'l10n_br_icms_uf_remet': sum([x['amount'] for x in icms_inter]),
            'l10n_br_icms_uf_dest': sum([x['amount'] for x in icms_intra]),
            'l10n_br_icms_fcp_uf_dest': sum([x['amount'] for x in icms_fcp]),
            'l10n_br_icms_valor_credito': (
                    base_icms_credito *
                    (self.l10n_br_icms_aliquota_credito / 100)),
            'l10n_br_ipi_base_calculo': sum([x['base'] for x in ipi]),
            'l10n_br_ipi_valor': sum([x['amount'] for x in ipi]),
            'l10n_br_pis_base_calculo': sum([x['base'] for x in pis]),
            'l10n_br_pis_valor': sum([x['amount'] for x in pis]),
            'l10n_br_cofins_base_calculo': sum([x['base'] for x in cofins]),
            'l10n_br_cofins_valor': sum([x['amount'] for x in cofins]),
            'l10n_br_issqn_base_calculo': sum([x['base'] for x in issqn]),
            'l10n_br_issqn_valor': sum([x['amount'] for x in issqn]),
            'l10n_br_ii_valor': sum([x['amount'] for x in ii]),
            'l10n_br_csll_base_calculo': sum([x['base'] for x in csll]),
            'l10n_br_csll_valor': sum([x['amount'] for x in csll]),
            'l10n_br_inss_base_calculo': sum([x['base'] for x in inss]),
            'l10n_br_inss_valor': sum([x['amount'] for x in inss]),
            'l10n_br_irrf_base_calculo': sum([x['base'] for x in irrf]),
            'l10n_br_irrf_valor': sum([x['amount'] for x in irrf]),
        })

    @api.multi
    @api.depends('l10n_br_icms_cst_normal', 'l10n_br_icms_csosn_simples',
                 'l10n_br_company_fiscal_type')
    def _compute_cst_icms(self):
        for item in self:
            item.l10n_br_icms_cst = (item.l10n_br_icms_cst_normal
                                     if item.l10n_br_company_fiscal_type == '3'
                                     else item.il10n_br_cms_csosn_simples)

    l10n_br_price_tax = fields.Float(
        compute='_compute_price', string='Impostos', store=True,
        digits=dp.get_precision('Account'),
        oldname='price_tax')
    price_total = fields.Float(
        u'Valor Líquido', digits=dp.get_precision('Account'), store=True,
        default=0.00, compute='_compute_price')
    l10n_br_valor_desconto = fields.Float(
        string='Vlr. desconto', store=True, compute='_compute_price',
        digits=dp.get_precision('Account'),
        oldname='valor_desconto')
    l10n_br_valor_bruto = fields.Float(
        string='Vlr. Bruto', store=True, compute='_compute_price',
        digits=dp.get_precision('Account'),
        oldname='valor_bruto')
    l10n_br_tributos_estimados = fields.Float(
        string='Total Est. Tributos', default=0.00,
        digits=dp.get_precision('Account'),
        oldname='tributos_estimados')
    l10n_br_tributos_estimados_federais = fields.Float(
        string='Tributos Federais', default=0.00,
        digits=dp.get_precision('Account'),
        oldname='tributos_estimados_federais')
    l10n_br_tributos_estimados_estaduais = fields.Float(
        string='Tributos Estaduais', default=0.00,
        digits=dp.get_precision('Account'),
        oldname='tributos_estimados_estaduais')
    l10n_br_tributos_estimados_municipais = fields.Float(
        string='Tributos Municipais', default=0.00,
        digits=dp.get_precision('Account'),
        oldname='tributos_estimados_municipais')

    l10n_br_rule_id = fields.Many2one('account.fiscal.position.tax.rule',
                                      'Regra', oldname='rule_id')
    l10n_br_cfop_id = fields.Many2one('br_account.cfop', 'CFOP',
                                      oldname='cfop_id')
    l10n_br_fiscal_classification_id = fields.Many2one(
        'product.fiscal.classification', u'Classificação Fiscal',
        oldname='fiscal_classification_id')
    l10n_br_product_type = fields.Selection(
        [('product', 'Produto'), ('service', u'Serviço')],
        string='Tipo do Produto', required=True, default='product',
        oldname='product_type')
    l10n_br_company_fiscal_type = fields.Selection(
        COMPANY_FISCAL_TYPE,
        default=_default_company_fiscal_type,
        string=u"Regime Tributário",
        oldname='company_fiscal_type')
    l10n_br_calculate_tax = fields.Boolean(string="Calcular Imposto?",
                                           default=True,
                                           oldname='calculate_tax')
    l10n_br_fiscal_comment = fields.Text(u'Observação Fiscal',
                                         oldname='fiscal_comment')

    # =========================================================================
    # ICMS Normal
    # =========================================================================
    l10n_br_icms_rule_id = fields.Many2one('account.fiscal.position.tax.rule',
                                           'Regra', oldname='icms_rule_id')
    l10n_br_tax_icms_id = fields.Many2one(
        'account.tax', string=u"Alíquota ICMS",
        domain=[('l10n_br_domain', '=', 'icms')], oldname='tax_icms_id')
    l10n_br_icms_cst = fields.Char('CST ICMS', size=10, store=True,
                                   compute='_compute_cst_icms',
                                   oldname='icms_cst')
    l10n_br_icms_cst_normal = fields.Selection(CST_ICMS, string="CST ICMS",
                                               oldname='icms_cst_normal')
    l10n_br_icms_origem = fields.Selection(
        ORIGEM_PROD, 'Origem', default='0', oldname='icms_origem')
    l10n_br_icms_tipo_base = fields.Selection(
        [('0', u'0 - Margem Valor Agregado (%)'),
         ('1', u'1 - Pauta (valor)'),
         ('2', u'2 - Preço Tabelado Máximo (valor)'),
         ('3', u'3 - Valor da Operação')],
        'Tipo Base ICMS', required=True, default='3', oldname='icms_tipo_base')
    l10n_br_incluir_ipi_base = fields.Boolean(
        string="Incl. Valor IPI?",
        help=u"Se marcado o valor do IPI inclui a base de cálculo",
        oldname='incluir_ipi_base')
    l10n_br_icms_base_calculo = fields.Float(
        'Base ICMS', required=True, compute='_compute_price', store=True,
        digits=dp.get_precision('Account'), default=0.00,
        oldname='icms_base_calculo')
    l10n_br_icms_valor = fields.Float(
        'Valor ICMS', required=True, compute='_compute_price', store=True,
        digits=dp.get_precision('Account'), default=0.00, oldname='icms_valor')
    l10n_br_icms_aliquota = fields.Float(
        'Perc ICMS', digits=dp.get_precision('Discount'), default=0.00,
        oldname='icms_aliquota')
    l10n_br_icms_aliquota_reducao_base = fields.Float(
        '% Red. Base ICMS', digits=dp.get_precision('Discount'),
        default=0.00, oldname='icms_aliquota_reducao_base')
    l10n_br_icms_base_calculo_manual = fields.Float(
        'Base ICMS Manual', digits=dp.get_precision('Account'), default=0.00,
        oldname='icms_base_calculo_manual')

    # =========================================================================
    # ICMS Substituição
    # =========================================================================
    l10n_br_tax_icms_st_id = fields.Many2one(
        'account.tax', string=u"Alíquota ICMS ST",
        domain=[('l10n_br_domain', '=', 'icmsst')], oldname='tax_icms_st_id')
    l10n_br_icms_st_tipo_base = fields.Selection(
        [('0', u'0 - Preço tabelado ou máximo  sugerido'),
         ('1', u'1 - Lista Negativa (valor)'),
         ('2', u'2 - Lista Positiva (valor)'),
         ('3', u'3 - Lista Neutra (valor)'),
         ('4', u'4 - Margem Valor Agregado (%)'),
         ('5', u'5 - Pauta (valor)')],
        'Tipo Base ICMS ST', required=True, default='4',
        oldname='icms_st_tipo_base')
    l10n_br_icms_st_valor = fields.Float(
        'Valor ICMS ST', required=True, compute='_compute_price', store=True,
        digits=dp.get_precision('Account'), default=0.00,
        oldname='icms_st_valor')
    l10n_br_icms_st_base_calculo = fields.Float(
        'Base ICMS ST', required=True, compute='_compute_price', store=True,
        digits=dp.get_precision('Account'), default=0.00,
        oldname='icms_st_base_calculo')
    l10n_br_icms_st_aliquota = fields.Float(
        '% ICMS ST', digits=dp.get_precision('Discount'),
        default=0.00, oldname='icms_st_aliquota')
    l10n_br_icms_st_aliquota_reducao_base = fields.Float(
        '% Red. Base ST',
        digits=dp.get_precision('Discount'),
        oldname='icms_st_aliquota_reducao_base')
    l10n_br_icms_st_aliquota_mva = fields.Float(
        'MVA Ajustado ST',
        digits=dp.get_precision('Discount'), default=0.00,
        oldname='icms_st_aliquota_mva')
    l10n_br_icms_st_base_calculo_manual = fields.Float(
        'Base ICMS ST Manual', digits=dp.get_precision('Account'),
        default=0.00, oldname='icms_st_base_calculo_manual')

    # =========================================================================
    # ICMS Difal
    # =========================================================================
    l10n_br_tem_difal = fields.Boolean(
        u'Difal?', digits=dp.get_precision('Discount'), oldname='tem_difal')
    l10n_br_icms_bc_uf_dest = fields.Float(
        u'Base ICMS', compute='_compute_price',
        digits=dp.get_precision('Discount'), oldname='icms_bc_uf_dest')
    l10n_br_tax_icms_inter_id = fields.Many2one(
        'account.tax', help=u"Alíquota utilizada na operação Interestadual",
        string="ICMS Inter", domain=[('l10n_br_domain', '=', 'icms_inter')],
        oldname='tax_icms_inter_id')
    l10n_br_tax_icms_intra_id = fields.Many2one(
        'account.tax', help=u"Alíquota interna do produto no estado destino",
        string="ICMS Intra", domain=[('l10n_br_domain', '=', 'icms_intra')],
        oldname='tax_icms_intra_id')
    l10n_br_tax_icms_fcp_id = fields.Many2one(
        'account.tax', string="% FCP", domain=[('l10n_br_domain', '=', 'fcp')],
        oldname='tax_icms_fcp_id')
    l10n_br_icms_aliquota_inter_part = fields.Float(
        u'% Partilha', default=80.0, digits=dp.get_precision('Discount'),
        oldname='icms_aliquota_inter_part')
    l10n_br_icms_fcp_uf_dest = fields.Float(
        string=u'Valor FCP', compute='_compute_price',
        digits=dp.get_precision('Discount'), oldname='icms_fcp_uf_dest')
    l10n_br_icms_uf_dest = fields.Float(
        u'ICMS Destino', compute='_compute_price',
        digits=dp.get_precision('Discount'), oldname='icms_uf_dest')
    l10n_br_icms_uf_remet = fields.Float(
        u'ICMS Remetente', compute='_compute_price',
        digits=dp.get_precision('Discount'), oldname='icms_uf_remet')

    # =========================================================================
    # ICMS Simples Nacional
    # =========================================================================
    l10n_br_icms_csosn_simples = fields.Selection(
        CSOSN_SIMPLES, string="CSOSN ICMS", oldname='icms_csosn_simples')
    l10n_br_icms_aliquota_credito = fields.Float(
        u"% Cŕedito ICMS", oldname='icms_aliquota_credito')
    l10n_br_icms_valor_credito = fields.Float(
        u"Valor de Crédito", compute='_compute_price', store=True,
        oldname='icms_valor_credito')
    l10n_br_icms_st_aliquota_deducao = fields.Float(
        string=u"% ICMS Próprio",
        help=u"Alíquota interna ou interestadual aplicada \
         sobre o valor da operação para deduzir do ICMS ST - Para empresas \
         do Simples Nacional ou usado em casos onde existe apenas ST sem ICMS",
        oldname='icms_st_aliquota_deducao')

    # =========================================================================
    # ISSQN
    # =========================================================================
    l10n_br_issqn_rule_id = fields.Many2one(
        'account.fiscal.position.tax.rule', 'Regra', oldname='issqn_rule_id')
    l10n_br_tax_issqn_id = fields.Many2one(
        'account.tax', string=u"Alíquota ISSQN",
        domain=[('l10n_br_domain', '=', 'issqn')], oldname='tax_issqn_id')
    l10n_br_issqn_tipo = fields.Selection(
        [('N', 'Normal'),
         ('R', 'Retida'),
         ('S', 'Substituta'),
         ('I', 'Isenta')],
        string='Tipo do ISSQN', required=True, default='N',
        oldname='issqn_tipo')
    l10n_br_service_type_id = fields.Many2one(
        'br_account.service.type', u'Tipo de Serviço',
        oldname='service_type_id')
    l10n_br_issqn_base_calculo = fields.Float(
        'Base ISSQN', digits=dp.get_precision('Account'),
        compute='_compute_price', store=True, oldname='issqn_base_calculo')
    l10n_br_issqn_aliquota = fields.Float(
        'Perc ISSQN', required=True, digits=dp.get_precision('Discount'),
        default=0.00, oldname='issqn_aliquota')
    l10n_br_issqn_valor = fields.Float(
        'Valor ISSQN', required=True, digits=dp.get_precision('Account'),
        default=0.00, compute='_compute_price', store=True,
        oldname='issqn_valor')
    l10n_br_issqn_deduction = fields.Float(
        '% Dedução Base ISSQN', digits=dp.get_precision('Discount'),
        default=0.00, store=True, oldname='issqn_deduction')

    # =========================================================================
    # IPI
    # =========================================================================
    l10n_br_ipi_rule_id = fields.Many2one('account.fiscal.position.tax.rule',
                                          'Regra', oldname='ipi_rule_id')
    l10n_br_tax_ipi_id = fields.Many2one(
        'account.tax', string=u"Alíquota IPI",
        domain=[('l10n_br_domain', '=', 'ipi')], oldname='tax_ipi_id')
    l10n_br_ipi_tipo = fields.Selection(
        [('percent', 'Percentual')],
        'Tipo do IPI', required=True, default='percent', oldname='ipi_tipo')
    l10n_br_ipi_base_calculo = fields.Float(
        'Base IPI', required=True, digits=dp.get_precision('Account'),
        default=0.00, compute='_compute_price', store=True,
        oldname='ipi_base_calculo')
    l10n_br_ipi_reducao_bc = fields.Float(
        u'% Redução Base', required=True, digits=dp.get_precision('Account'),
        default=0.00, oldname='ipi_reducao_bc')
    l10n_br_ipi_valor = fields.Float(
        'Valor IPI', required=True, digits=dp.get_precision('Account'),
        default=0.00, compute='_compute_price', store=True,
        oldname='ipi_valor')
    l10n_br_ipi_aliquota = fields.Float(
        'Perc IPI', required=True, digits=dp.get_precision('Discount'),
        default=0.00, oldname='ipi_aliquota')
    l10n_br_ipi_cst = fields.Selection(CST_IPI, string='CST IPI',
                                       oldname='ipi_cst')
    l10n_br_ipi_base_calculo_manual = fields.Float(
        'Base IPI Manual', digits=dp.get_precision('Account'), default=0.00,
        oldname='ipi_base_calculo_manual')

    # =========================================================================
    # PIS
    # =========================================================================
    l10n_br_pis_rule_id = fields.Many2one('account.fiscal.position.tax.rule',
                                          'Regra', oldname='pis_rule_id')
    l10n_br_tax_pis_id = fields.Many2one(
        'account.tax', string=u"Alíquota PIS",
        domain=[('l10n_br_domain', '=', 'pis')], oldname='tax_pis_id')
    l10n_br_pis_cst = fields.Selection(CST_PIS_COFINS, 'CST PIS',
                                       oldname='pis_cst')
    l10n_br_pis_tipo = fields.Selection(
        [('percent', 'Percentual')],
        string='Tipo do PIS', required=True, default='percent',
        oldname='pis_tipo')
    l10n_br_pis_base_calculo = fields.Float(
        'Base PIS', required=True, compute='_compute_price', store=True,
        digits=dp.get_precision('Account'), default=0.00,
        oldname='pis_base_calculo')
    l10n_br_pis_valor = fields.Float(
        'Valor PIS', required=True, digits=dp.get_precision('Account'),
        default=0.00, compute='_compute_price', store=True,
        oldname='pis_valor')
    l10n_br_pis_aliquota = fields.Float(
        'Perc PIS', required=True, digits=dp.get_precision('Discount'),
        default=0.00, oldname='pis_aliquota')
    l10n_br_pis_base_calculo_manual = fields.Float(
        'Base PIS Manual', digits=dp.get_precision('Account'), default=0.00,
        oldname='pis_base_calculo_manual')

    # =========================================================================
    # COFINS
    # =========================================================================
    l10n_br_cofins_rule_id = fields.Many2one(
        'account.fiscal.position.tax.rule', 'Regra',
        oldname='cofins_rule_id')
    l10n_br_tax_cofins_id = fields.Many2one(
        'account.tax', string=u"Alíquota COFINS",
        domain=[('l10n_br_domain', '=', 'cofins')],
        oldname='tax_cofins_id')
    l10n_br_cofins_cst = fields.Selection(
        CST_PIS_COFINS, 'CST COFINS', oldname='cofins_cst')
    l10n_br_cofins_tipo = fields.Selection(
        [('percent', 'Percentual')],
        string='Tipo do COFINS', required=True, default='percent',
        oldname='cofins_tipo')
    l10n_br_cofins_base_calculo = fields.Float(
        'Base COFINS', compute='_compute_price', store=True,
        digits=dp.get_precision('Account'), oldname='cofins_base_calculo')
    l10n_br_cofins_valor = fields.Float(
        'Valor COFINS', digits=dp.get_precision('Account'),
        compute='_compute_price', store=True,
        oldname='cofins_valor')
    l10n_br_cofins_aliquota = fields.Float(
        'Perc COFINS', digits=dp.get_precision('Discount'),
        oldname='cofins_aliquota')
    l10n_br_cofins_base_calculo_manual = fields.Float(
        'Base COFINS Manual', digits=dp.get_precision('Account'), default=0.00,
        oldname='cofins_base_calculo_manual')

    # =========================================================================
    # Imposto de importação
    # =========================================================================
    l10n_br_ii_rule_id = fields.Many2one('account.fiscal.position.tax.rule',
                                         'Regra', oldname='ii_rule_id')
    l10n_br_tax_ii_id = fields.Many2one(
        'account.tax', string=u"Alíquota II",
        domain=[('l10n_br_domain', '=', 'ii')], oldname='tax_ii_id')
    l10n_br_ii_base_calculo = fields.Float(
        'Base II', required=True, digits=dp.get_precision('Account'),
        default=0.00, store=True, oldname='ii_base_calculo')
    l10n_br_ii_aliquota = fields.Float(
        '% II', required=True, digits=dp.get_precision('Account'),
        default=0.00, oldname='ii_aliquota')
    l10n_br_ii_valor = fields.Float(
        'Valor II', required=True, digits=dp.get_precision('Account'),
        default=0.00, compute='_compute_price', store=True,
        oldname='ii_valor')
    l10n_br_ii_valor_iof = fields.Float(
        'Valor IOF', required=True, digits=dp.get_precision('Account'),
        default=0.00, oldname='ii_valor_iof')
    l10n_br_ii_valor_despesas = fields.Float(
        'Desp. Aduaneiras', required=True,
        digits=dp.get_precision('Account'), default=0.00,
        oldname='ii_valor_despesas')
    l10n_br_import_declaration_ids = fields.One2many(
        'br_account.import.declaration',
        'invoice_line_id', u'Declaração de Importação',
        oldname='import_declaration_ids')

    # =========================================================================
    # Impostos de serviço - CSLL
    # =========================================================================
    l10n_br_csll_rule_id = fields.Many2one('account.fiscal.position.tax.rule',
                                           'Regra', oldname='csll_rule_id')
    l10n_br_tax_csll_id = fields.Many2one(
        'account.tax', string=u"Alíquota CSLL",
        domain=[('l10n_br_domain', '=', 'csll')], oldname='tax_csll_id')
    l10n_br_csll_base_calculo = fields.Float(
        'Base CSLL', required=True, digits=dp.get_precision('Account'),
        default=0.00, compute='_compute_price', store=True,
        oldname='csll_base_calculo')
    l10n_br_csll_valor = fields.Float(
        'Valor CSLL', required=True, digits=dp.get_precision('Account'),
        default=0.00, compute='_compute_price', store=True,
        oldname='csll_valor')
    l10n_br_csll_aliquota = fields.Float(
        'Perc CSLL', required=True, digits=dp.get_precision('Account'),
        default=0.00, oldname='csll_aliquota')

    # =========================================================================
    # Impostos de serviço - IRRF
    # =========================================================================
    l10n_br_irrf_rule_id = fields.Many2one('account.fiscal.position.tax.rule',
                                           'Regra', oldname='irrf_rule_id')
    l10n_br_tax_irrf_id = fields.Many2one(
        'account.tax', string=u"Alíquota IRRF",
        domain=[('l10n_br_domain', '=', 'irrf')], oldname='tax_irrf_id')
    l10n_br_irrf_base_calculo = fields.Float(
        'Base IRRF', required=True, digits=dp.get_precision('Account'),
        default=0.00, compute='_compute_price', store=True,
        oldname='irrf_base_calculo')
    l10n_br_irrf_valor = fields.Float(
        'Valor IRFF', required=True, digits=dp.get_precision('Account'),
        default=0.00, compute='_compute_price', store=True,
        oldname='irrf_valor')
    l10n_br_irrf_aliquota = fields.Float(
        'Perc IRRF', required=True, digits=dp.get_precision('Account'),
        default=0.00, oldname='irrf_aliquota')

    # =========================================================================
    # Impostos de serviço - INSS
    # =========================================================================
    l10n_br_inss_rule_id = fields.Many2one('account.fiscal.position.tax.rule',
                                           'Regra', oldname='inss_rule_id')
    l10n_br_tax_inss_id = fields.Many2one(
        'account.tax', string=u"Alíquota IRRF",
        domain=[('l10n_br_domain', '=', 'inss')], oldname='tax_inss_id')
    l10n_br_inss_base_calculo = fields.Float(
        u'Base INSS', required=True, digits=dp.get_precision('Account'),
        default=0.00, compute='_compute_price', store=True,
        oldname='inss_base_calculo')
    l10n_br_inss_valor = fields.Float(
        u'Valor INSS', required=True, digits=dp.get_precision('Account'),
        default=0.00, compute='_compute_price', store=True,
        oldname='inss_valor')
    l10n_br_inss_aliquota = fields.Float(
        u'Perc INSS', required=True, digits=dp.get_precision('Account'),
        default=0.00, oldname='inss_aliquota')

    l10n_br_informacao_adicional = fields.Text(
        string=u"Informações Adicionais", oldname='informacao_adicional')

    def _update_tax_from_ncm(self):
        if self.product_id:
            ncm = self.product_id.l10n_br_fiscal_classification_id
            self.update({
                'l10n_br_icms_st_aliquota_mva': ncm.icms_st_aliquota_mva,
                'l10n_br_icms_st_aliquota_reducao_base':
                    ncm.icms_st_aliquota_reducao_base,
                'l10n_br_ipi_cst': ncm.ipi_cst,
                'l10n_br_ipi_reducao_bc': ncm.ipi_reducao_bc,
                'l10n_br_tax_icms_st_id': ncm.tax_icms_st_id.id,
                'l10n_br_tax_ipi_id': ncm.tax_ipi_id.id,
            })

    def _set_taxes(self):
        super(AccountInvoiceLine, self)._set_taxes()
        self._update_tax_from_ncm()
        fpos = self.invoice_id.fiscal_position_id
        if fpos:
            vals = fpos.map_tax_extra_values(
                self.company_id, self.product_id, self.invoice_id.partner_id)

            for key, value in vals.items():
                if value and key in self._fields:
                    self.update({key: value})

        self.invoice_line_tax_ids = \
            self.l10n_br_tax_icms_id | self.l10n_br_tax_icms_st_id | \
            self.l10n_br_tax_icms_inter_id | self.l10n_br_tax_icms_intra_id | \
            self.l10n_br_tax_icms_fcp_id | self.l10n_br_tax_ipi_id | \
            self.l10n_br_tax_pis_id | self.l10n_br_tax_cofins_id | \
            self.l10n_br_tax_issqn_id | self.l10n_br_tax_ii_id | \
            self.l10n_br_tax_csll_id | self.l10n_br_tax_irrf_id | \
            self.l10n_br_tax_inss_id

    def _set_extimated_taxes(self, price):
        service = self.product_id.l10n_br_service_type_id
        ncm = self.product_id.l10n_br_fiscal_classification_id

        if self.l10n_br_product_type == 'service':
            self.l10n_br_tributos_estimados_federais = (
                price * (service.federal_nacional / 100))
            self.l10n_br_tributos_estimados_estaduais = (
                price * (service.estadual_imposto / 100))
            self.l10n_br_tributos_estimados_municipais = (
                price * (service.municipal_imposto / 100))
        else:
            federal = ncm.federal_nacional \
                if self.l10n_br_icms_origem in ('1', '2', '3', '8') \
                else ncm.federal_importado

            self.l10n_br_tributos_estimados_federais = price * (federal / 100)
            self.l10n_br_tributos_estimados_estaduais = (
                price * (ncm.estadual_imposto / 100))
            self.l10n_br_tributos_estimados_municipais = (
                price * (ncm.municipal_imposto / 100))

        self.l10n_br_tributos_estimados = (
            self.l10n_br_tributos_estimados_federais +
            self.l10n_br_tributos_estimados_estaduais +
            self.l10n_br_tributos_estimados_municipais
        )

    @api.onchange('price_subtotal')
    def _br_account_onchange_quantity(self):
        self._set_extimated_taxes(self.price_subtotal)

    @api.onchange('product_id')
    def _br_account_onchange_product_id(self):
        self.l10n_br_product_type = self.product_id.l10n_br_fiscal_type
        self.l10n_br_icms_origem = self.product_id.l10n_br_origin
        ncm = self.product_id.l10n_br_fiscal_classification_id
        service = self.product_id.l10n_br_service_type_id
        self.l10n_br_fiscal_classification_id = ncm.id
        self.l10n_br_service_type_id = service.id

        self._set_extimated_taxes(self.product_id.lst_price)

    def _update_invoice_line_ids(self):
        other_taxes = self.invoice_line_tax_ids.filtered(
            lambda x: not x.l10n_br_domain)
        self.invoice_line_tax_ids = (
            other_taxes | self.l10n_br_tax_icms_id |
            self.l10n_br_tax_icms_st_id | self.l10n_br_tax_icms_inter_id |
            self.l10n_br_tax_icms_intra_id | self.l10n_br_tax_icms_fcp_id |
            self.l10n_br_tax_ipi_id | self.l10n_br_tax_pis_id |
            self.l10n_br_tax_cofins_id | self.l10n_br_tax_issqn_id |
            self.l10n_br_tax_ii_id | self.l10n_br_tax_csll_id |
            self.l10n_br_tax_irrf_id | self.l10n_br_tax_inss_id
        )

    @api.onchange('l10n_br_tax_icms_id')
    def _onchange_tax_icms_id(self):
        if self.l10n_br_tax_icms_id:
            self.l10n_br_icms_aliquota = self.l10n_br_tax_icms_id.amount
        self._update_invoice_line_ids()

    @api.onchange('l10n_br_tax_icms_st_id')
    def _onchange_tax_icms_st_id(self):
        if self.l10n_br_tax_icms_st_id:
            self.l10n_br_icms_st_aliquota = self.l10n_br_tax_icms_st_id.amount
        self._update_invoice_line_ids()

    @api.onchange('l10n_br_tax_icms_inter_id')
    def _onchange_tax_icms_inter_id(self):
        self._update_invoice_line_ids()

    @api.onchange('l10n_br_tax_icms_intra_id')
    def _onchange_tax_icms_intra_id(self):
        self._update_invoice_line_ids()

    @api.onchange('l10n_br_tax_icms_fcp_id')
    def _onchange_tax_icms_fcp_id(self):
        self._update_invoice_line_ids()

    @api.onchange('l10n_br_tax_pis_id')
    def _onchange_tax_pis_id(self):
        if self.l10n_br_tax_pis_id:
            self.l10n_br_pis_aliquota = self.l10n_br_tax_pis_id.amount
        self._update_invoice_line_ids()

    @api.onchange('l10n_br_tax_cofins_id')
    def _onchange_tax_cofins_id(self):
        if self.l10n_br_tax_cofins_id:
            self.l10n_br_cofins_aliquota = self.l10n_br_tax_cofins_id.amount
        self._update_invoice_line_ids()

    @api.onchange('l10n_br_tax_ipi_id')
    def _onchange_tax_ipi_id(self):
        if self.l10n_br_tax_ipi_id:
            self.l10n_br_ipi_aliquota = self.l10n_br_tax_ipi_id.amount
        self._update_invoice_line_ids()

    @api.onchange('l10n_br_tax_ii_id')
    def _onchange_tax_ii_id(self):
        if self.l10n_br_tax_ii_id:
            self.l10n_br_ii_aliquota = self.l10n_br_tax_ii_id.amount
        self._update_invoice_line_ids()

    @api.onchange('l10n_br_tax_issqn_id')
    def _onchange_tax_issqn_id(self):
        if self.l10n_br_tax_issqn_id:
            self.l10n_br_issqn_aliquota = self.l10n_br_tax_issqn_id.amount
        self._update_invoice_line_ids()

    @api.onchange('l10n_br_tax_csll_id')
    def _onchange_tax_csll_id(self):
        if self.l10n_br_tax_csll_id:
            self.l10n_br_csll_aliquota = self.l10n_br_tax_csll_id.amount
        self._update_invoice_line_ids()

    @api.onchange('l10n_br_tax_irrf_id')
    def _onchange_tax_irrf_id(self):
        if self.l10n_br_tax_irrf_id:
            self.l10n_br_irrf_aliquota = self.l10n_br_tax_irrf_id.amount
        self._update_invoice_line_ids()

    @api.onchange('l10n_br_tax_inss_id')
    def _onchange_tax_inss_id(self):
        if self.l10n_br_tax_inss_id:
            self.l10n_br_inss_aliquota = self.l10n_br_tax_inss_id.amount
        self._update_invoice_line_ids()
