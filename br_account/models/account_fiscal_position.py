# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from openerp import api, fields, models
from odoo.addons.br_account.models.cst import CST_ICMS
from odoo.addons.br_account.models.cst import CST_IPI
from odoo.addons.br_account.models.cst import CST_PIS_COFINS


class AccountFiscalPositionTaxRule(models.Model):
    _name = 'account.fiscal.position.tax.rule'

    name = fields.Char(string="Descrição", size=100)
    domain = fields.Selection([('icms', 'ICMS'),
                               ('pis', 'PIS'),
                               ('cofins', 'COFINS'),
                               ('ipi', 'IPI'),
                               ('issqn', 'ISSQN'),
                               ('ii', 'II'),
                               ('outros', 'Outros')], string="Tipo")
    fiscal_position_id = fields.Many2one(
        'account.fiscal.position', string="Posição Fiscal")
    state_ids = fields.Many2many('res.country.state', string="Estado destino")
    product_category_ids = fields.Many2many(
        'product.category', string="Categoria de Produtos")
    product_ids = fields.Many2many('product.product', string="Produtos")
    partner_ids = fields.Many2many('res.partner', string="Parceiros")

    cst_icms = fields.Selection(CST_ICMS, string="CST ICMS")
    cst_pis = fields.Selection(CST_PIS_COFINS, string="CST PIS")
    cst_cofins = fields.Selection(CST_PIS_COFINS, string="CST COFINS")
    cst_ipi = fields.Selection(CST_IPI, string="CST IPI")
    cfop_id = fields.Many2one('br_account.cfop', string="CFOP")
    tax_id = fields.Many2one('account.tax', string="Imposto")
    tax_icms_st_id = fields.Many2one('account.tax', string="ICMS ST",
                                     domain=[('domain', '=', 'icmsst')])
    reducao_base = fields.Float(string="Redução de base")
    reducao_base_st = fields.Float(string="Redução de base ST")
    aliquota_mva = fields.Float(string="Alíquota MVA")


class AccountFiscalPosition(models.Model):
    _inherit = 'account.fiscal.position'

    note = fields.Text('Observações')

    icms_tax_rule_ids = fields.One2many(
        'account.fiscal.position.tax.rule', 'fiscal_position_id',
        string="Regras ICMS", domain=[('domain', '=', 'icms')])
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

    @api.model
    def map_tax_extra_values(self, company, product, partner):
        rule_obj = self.env['account.fiscal.position.tax.rule']

        to_state = partner.state_id.id
        product_id = product.id
        partner_id = partner.id
        domain = [('fiscal_position_id', '=', self.id)]
        domain += [('partner_ids', '=', partner_id)]
        rules = rule_obj.search(domain)
        if not rules:
            domain.pop()
            domain += [('product_ids', '=', product_id)]
            rules = rule_obj.search(domain)
        if not rules:
            domain.pop()
            domain += [('state_ids', '=', to_state)]
            rules = rule_obj.search(domain)
        if not rules:
            domain.pop()
            rules = rule_obj.search(domain)
        if rules:
            return {
                'rule_id': rules[0],
                'cfop_id': rules[0].cfop_id,
                'icms_cst_normal': rules[0].cst_icms,
                'tax_icms_id': rules[0].tax_id,
            }
        else:
            return {}
