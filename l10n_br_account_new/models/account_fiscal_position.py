# -*- coding: utf-8 -*-
# © 2009 Renato Lima - Akretion
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from openerp import fields, models


class AccountFiscalPositionTemplate(models.Model):
    _inherit = 'account.fiscal.position.template'

    fiscal_category_fiscal_type = fields.Selection(
        [('service', u'Serviço'), ('product', 'Produto')],
        string='Fiscal Type')
    type = fields.Selection(
        [('input', 'Entrada'), ('output', 'Saida')], 'Tipo')


class AccountFiscalPosition(models.Model):
    _inherit = 'account.fiscal.position'

    note = fields.Text('Observações')  # TODO Fazer este campo gerar mensagens dinamicas


class AccountFiscalPositionTax(models.Model):
    _inherit = 'account.fiscal.position.tax'

    state_ids = fields.Many2many('res.country.state', string="Estados")
