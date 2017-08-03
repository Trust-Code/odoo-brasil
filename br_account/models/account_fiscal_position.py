# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import api, fields, models
from odoo.addons.br_account.models.cst import CST_ICMS
from odoo.addons.br_account.models.cst import CSOSN_SIMPLES
from odoo.addons.br_account.models.cst import CST_IPI
from odoo.addons.br_account.models.cst import CST_PIS_COFINS


class AccountFiscalPositionTaxRule(models.Model):
    _name = 'account.fiscal.position.tax.rule'
    _order = 'sequence'

    sequence = fields.Integer(string=u"Sequência")
    name = fields.Char(string=u"Descrição", size=100)
    domain = fields.Selection([('icms', 'ICMS'),
                               ('simples', 'Simples Nacional'),
                               ('pis', 'PIS'),
                               ('cofins', 'COFINS'),
                               ('ipi', 'IPI'),
                               ('issqn', 'ISSQN'),
                               ('ii', 'II'),
                               ('csll', 'CSLL'),
                               ('irrf', 'IRRF'),
                               ('inss', 'INSS'),
                               ('outros', 'Outros')], string="Tipo")
    fiscal_position_id = fields.Many2one(
        'account.fiscal.position', string=u"Posição Fiscal")

    state_ids = fields.Many2many('res.country.state', string="Estado Destino",
                                 domain=[('country_id.code', '=', 'BR')])
    product_category_ids = fields.Many2many(
        'product.category', string="Categoria de Produtos")
    tipo_produto = fields.Selection([('product', 'Produto'),
                                     ('service', u'Serviço')],
                                    string="Tipo produto", default="product")

    product_ids = fields.Many2many('product.product', string="Produtos")
    partner_ids = fields.Many2many('res.partner', string="Parceiros")

    cst_icms = fields.Selection(CST_ICMS, string="CST ICMS")
    csosn_icms = fields.Selection(CSOSN_SIMPLES, string="CSOSN ICMS")
    cst_pis = fields.Selection(CST_PIS_COFINS, string="CST PIS")
    cst_cofins = fields.Selection(CST_PIS_COFINS, string="CST COFINS")
    cst_ipi = fields.Selection(CST_IPI, string="CST IPI")
    cfop_id = fields.Many2one('br_account.cfop', string="CFOP")
    tax_id = fields.Many2one('account.tax', string="Imposto")
    tax_icms_st_id = fields.Many2one('account.tax', string="ICMS ST",
                                     domain=[('domain', '=', 'icmsst')])
    icms_aliquota_credito = fields.Float(string=u"% Crédito de ICMS")
    incluir_ipi_base = fields.Boolean(string="Incl. IPI na base ICMS")
    reducao_icms = fields.Float(string=u"Redução de base")
    reducao_icms_st = fields.Float(string=u"Redução de base ST")
    reducao_ipi = fields.Float(string=u"Redução de base IPI")
    aliquota_mva = fields.Float(string=u"Alíquota MVA")
    icms_st_aliquota_deducao = fields.Float(
        string=u"% ICMS Próprio",
        help="Alíquota interna ou interestadual aplicada \
         sobre o valor da operação para deduzir do ICMS ST - Para empresas \
         do Simples Nacional ou usado em casos onde existe apenas ST sem ICMS")
    tem_difal = fields.Boolean(string="Aplicar Difal?")
    tax_icms_inter_id = fields.Many2one(
        'account.tax', help=u"Alíquota utilizada na operação Interestadual",
        string="ICMS Inter", domain=[('domain', '=', 'icms_inter')])
    tax_icms_intra_id = fields.Many2one(
        'account.tax', help=u"Alíquota interna do produto no estado destino",
        string="ICMS Intra", domain=[('domain', '=', 'icms_intra')])
    tax_icms_fcp_id = fields.Many2one(
        'account.tax', string="% FCP", domain=[('domain', '=', 'fcp')])


class AccountFiscalPosition(models.Model):
    _inherit = 'account.fiscal.position'

    journal_id = fields.Many2one(
        'account.journal', string="Diário Contábil",
        help="Diário Contábil a ser utilizado na fatura.")
    account_id = fields.Many2one(
        'account.account', string="Conta Contábil",
        help="Conta Contábil a ser utilizada na fatura.")
    fiscal_observation_ids = fields.Many2many(
        'br_account.fiscal.observation', string="Mensagens Doc. Eletrônico")
    note = fields.Text(u'Observações')

    icms_tax_rule_ids = fields.One2many(
        'account.fiscal.position.tax.rule', 'fiscal_position_id',
        string="Regras ICMS", domain=[('domain', '=', 'icms')])
    simples_tax_rule_ids = fields.One2many(
        'account.fiscal.position.tax.rule', 'fiscal_position_id',
        string="Regras Simples Nacional", domain=[('domain', '=', 'simples')])
    ipi_tax_rule_ids = fields.One2many(
        'account.fiscal.position.tax.rule', 'fiscal_position_id',
        string="Regras IPI", domain=[('domain', '=', 'ipi')])
    pis_tax_rule_ids = fields.One2many(
        'account.fiscal.position.tax.rule', 'fiscal_position_id',
        string="Regras PIS", domain=[('domain', '=', 'pis')])
    cofins_tax_rule_ids = fields.One2many(
        'account.fiscal.position.tax.rule', 'fiscal_position_id',
        string="Regras COFINS", domain=[('domain', '=', 'cofins')])
    issqn_tax_rule_ids = fields.One2many(
        'account.fiscal.position.tax.rule', 'fiscal_position_id',
        string="Regras ISSQN", domain=[('domain', '=', 'issqn')])
    ii_tax_rule_ids = fields.One2many(
        'account.fiscal.position.tax.rule', 'fiscal_position_id',
        string="Regras II", domain=[('domain', '=', 'ii')])
    irrf_tax_rule_ids = fields.One2many(
        'account.fiscal.position.tax.rule', 'fiscal_position_id',
        string="Regras IRRF", domain=[('domain', '=', 'irrf')])
    csll_tax_rule_ids = fields.One2many(
        'account.fiscal.position.tax.rule', 'fiscal_position_id',
        string="Regras CSLL", domain=[('domain', '=', 'csll')])
    inss_tax_rule_ids = fields.One2many(
        'account.fiscal.position.tax.rule', 'fiscal_position_id',
        string="Regras INSS", domain=[('domain', '=', 'inss')])

    def _filter_rules(self, fpos_id, type_tax, partner, product, state):
        rule_obj = self.env['account.fiscal.position.tax.rule']
        domain = [('fiscal_position_id', '=', fpos_id),
                  ('domain', '=', type_tax)]
        rules = rule_obj.search(domain)
        if rules:
            rules_points = {}
            for rule in rules:
                rules_points[rule.id] = 0
                if rule.tipo_produto == product.fiscal_type:
                    rules_points[rule.id] += 1
                if state in rule.state_ids:
                    rules_points[rule.id] += 1
                if product.categ_id in rule.product_category_ids:
                    rules_points[rule.id] += 1
                if product in rule.product_ids:
                    rules_points[rule.id] += 1
                if len(rule.product_ids) > 0:
                    rules_points[rule.id] -= 1
                if not rule.tipo_produto:
                    rules_points[rule.id] -= 1
                if len(rule.product_category_ids) > 0:
                    rules_points[rule.id] -= 1
                if len(rule.state_ids) > 0:
                    rules_points[rule.id] -= 1
            greater_rule = max([(v, k) for k, v in rules_points.items()])
            if greater_rule[0] <= 0:
                return {}
            rules = [rules.browse(greater_rule[1])]

            return {
                ('%s_rule_id' % type_tax): rules[0],
                'cfop_id': rules[0].cfop_id,
                ('tax_%s_id' % type_tax): rules[0].tax_id,
                # ICMS
                'icms_cst_normal': rules[0].cst_icms,
                'icms_aliquota_reducao_base': rules[0].reducao_icms,
                'incluir_ipi_base': rules[0].incluir_ipi_base,
                # ICMS ST
                'tax_icms_st_id': rules[0].tax_icms_st_id,
                'icms_st_aliquota_mva': rules[0].aliquota_mva,
                'icms_st_aliquota_reducao_base': rules[0].reducao_icms_st,
                'icms_st_aliquota_deducao': rules[0].icms_st_aliquota_deducao,
                # ICMS Difal
                'tem_difal': rules[0].tem_difal,
                'tax_icms_inter_id': rules[0].tax_icms_inter_id,
                'tax_icms_intra_id': rules[0].tax_icms_intra_id,
                'tax_icms_fcp_id': rules[0].tax_icms_fcp_id,
                # Simples
                'icms_csosn_simples': rules[0].csosn_icms,
                'icms_aliquota_credito': rules[0].icms_aliquota_credito,
                # IPI
                'ipi_cst': rules[0].cst_ipi,
                'ipi_reducao_bc': rules[0].reducao_ipi,
                # PIS
                'pis_cst': rules[0].cst_pis,
                # PIS
                'cofins_cst': rules[0].cst_cofins,
            }
        else:
            return {}

    @api.model
    def map_tax_extra_values(self, company, product, partner):
        to_state = partner.state_id

        taxes = ('icms', 'simples', 'ipi', 'pis', 'cofins',
                 'issqn', 'ii', 'irrf', 'csll', 'inss')
        res = {}
        for tax in taxes:
            vals = self._filter_rules(
                self.id, tax, partner, product, to_state)
            res.update({k: v for k, v in vals.items() if v})

        return res
