# -*- coding: utf-8 -*-
# © 2009 Renato Lima - Akretion
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from openerp import fields, models


class AccountFiscalPosition(models.Model):
    _inherit = 'account.fiscal.position'

    fiscal_category_fiscal_type = fields.Selection(
        [('service', u'Serviço'), ('product', 'Produto')],
        string='Fiscal Type')
    type = fields.Selection(
        [('input', 'Entrada'), ('output', 'Saida')], 'Tipo')
    inv_copy_note = fields.Boolean('Copiar Observação na Nota Fiscal')
    note = fields.Text('Observações')
