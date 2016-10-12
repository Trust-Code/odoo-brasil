# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from openerp import fields, models


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
    cfop = fields.Many2one('br_account.cfop', string="CFOP")
    tax_id = fields.Many2one('account.tax', string="Imposto")


class AccountFiscalPosition(models.Model):
    _inherit = 'account.fiscal.position'

    note = fields.Text('Observações')

    tax_rule_ids = fields.One2many(
        'account.fiscal.position.tax.rule', 'fiscal_position_id',
        string="Regras")
