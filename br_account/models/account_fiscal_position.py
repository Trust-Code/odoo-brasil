# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from openerp import api, fields, models


class AccountFiscalPositionTaxRule(models.Model):
    _name = 'account.fiscal.position.tax.rule'

    name = fields.Char(string="Descrição", size=100)
    fiscal_position_id = fields.Many2one(
        'account.fiscal.position', string="Posição Fiscal")
    state_ids = fields.Many2many('res.country.state', string="Estado destino")
    product_category_ids = fields.Many2many(
        'product.category', string="Categoria de Produtos")
    product_ids = fields.Many2many('product.product', string="Produtos")
    partner_ids = fields.Many2many('res.partner', string="Parceiros")

    cst_to_use = fields.Char(string="CST")
    cfop_id = fields.Many2one('br_account.cfop', string="CFOP")
    tax_id = fields.Many2one('account.tax', string="Imposto")


class AccountFiscalPosition(models.Model):
    _inherit = 'account.fiscal.position'

    note = fields.Text('Observações')

    tax_rule_ids = fields.One2many(
        'account.fiscal.position.tax.rule', 'fiscal_position_id',
        string="Regras")

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
                'icms_cst_normal': rules[0].cst_to_use,
                'tax_icms_id': rules[0].tax_id,
            }
        else:
            return {}
