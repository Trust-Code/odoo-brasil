# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from openerp import api, fields, models
from odoo.addons.br_account.models.cst import CST_ICMS
from odoo.addons.br_account.models.cst import CST_IPI
from odoo.addons.br_account.models.cst import CST_PIS_COFINS
from odoo.addons.br_account.models.cst import ORIGEM_PROD


class AccountFiscalPositionTaxRule(models.Model):
    _name = 'account.fiscal.position.tax.rule'
    _order = 'sequence'

    sequence = fields.Integer(string="Sequência")
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

    state_ids = fields.Many2many('res.country.state', string="Estado destino",
                                 domain=[('country_id.code', '=', 'BR')])
    product_category_ids = fields.Many2many(
        'product.category', string="Categoria de Produtos")
    origem_produto = fields.Selection(ORIGEM_PROD, string="Origem do Produto")
    tipo_produto = fields.Selection([('product', 'Produto'),
                                     ('service', 'Serviço')],
                                    string="Tipo produto", default="product")
    consumidor_final = fields.Selection([('0', u'Não'), ('1', u'Sim')],
                                        string="Consumidor Final")

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

    def _filter_rules(self, fpos_id, type_tax, partner,
                      product, state):
        rule_obj = self.env['account.fiscal.position.tax.rule']
        domain = ['|', ('tipo_produto', '=', product.fiscal_type),
                  ('tipo_produto', '=', False),
                  ('fiscal_position_id', '=', fpos_id),
                  ('domain', '=', type_tax)]
        domain += [('partner_ids', '=', partner.id)]
        rules = rule_obj.search(domain)
        if not rules:
            domain.pop()
            domain += [('product_ids', '=', product.id)]
            rules = rule_obj.search(domain)
        if not rules:
            domain.pop()
            domain += [('state_ids', '=', state.id)]
            rules = rule_obj.search(domain)
        if not rules:
            domain.pop()
            rules = rule_obj.search(domain)
        if rules:
            return {
                ('%s_rule_id' % type_tax): rules[0],
                'cfop_id': rules[0].cfop_id,
                ('tax_%s_id' % type_tax): rules[0].tax_id,
                # ICMS
                'icms_cst_normal': rules[0].cst_icms,
                'icms_aliquota_reducao_base': rules[0].reducao_base,
                # ICMS ST
                'tax_icms_st_id': rules[0].tax_icms_st_id,
                'icms_st_aliquota_mva': rules[0].aliquota_mva,
                'icms_st_aliquota_reducao_base': rules[0].reducao_base_st,
                # IPI
                'ipi_cst': rules[0].cst_ipi,
                'ipi_reducao_bc': rules[0].reducao_base,
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

        res = {}
        vals = self._filter_rules(
            self.id, 'icms', partner, product, to_state)
        res.update({k: v for k, v in vals.items() if v})

        vals = self._filter_rules(
            self.id, 'ipi', partner, product, to_state)
        res.update({k: v for k, v in vals.items() if v})

        vals = self._filter_rules(
            self.id, 'pis', partner, product, to_state)
        res.update({k: v for k, v in vals.items() if v})

        vals = self._filter_rules(
            self.id, 'cofins', partner, product, to_state)
        res.update({k: v for k, v in vals.items() if v})

        vals = self._filter_rules(
            self.id, 'issqn', partner, product, to_state)
        res.update({k: v for k, v in vals.items() if v})

        vals = self._filter_rules(
            self.id, 'ii', partner, product, to_state)
        res.update({k: v for k, v in vals.items() if v})

        return res
