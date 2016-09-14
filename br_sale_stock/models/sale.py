# -*- coding: utf-8 -*-
# © 2014  Renato Lima - Akretion
# © 2013  Raphaël Valyi - Akretion
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import fields, models
from odoo.addons import decimal_precision as dp


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    amount_freight = fields.Float(
        string='Frete', default=0.00, digits=dp.get_precision('Account'),
        readonly=True, states={'draft': [('readonly', False)]})


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    freight_value = fields.Float('Freight',
                                 default=0.0,
                                 digits=dp.get_precision('Account'))
