# -*- coding: utf-8 -*-
# © 2009  Renato Lima - Akretion
# © 2012  Raphaël Valyi - Akretion
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError


def calc_price_ratio(preco_bruto, quantidade, total):
    if total:
        return preco_bruto * quantidade / total
    else:
        return 0.0


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    amount_costs = fields.Float(
        string='Outros Custos', default=0.00,
        digits=dp.get_precision('Account'),
        readonly=True, states={'draft': [('readonly', False)]})
    amount_insurance = fields.Float(
        string='Seguro', default=0.00, digits=dp.get_precision('Account'),
        readonly=True, states={'draft': [('readonly', False)]})
    amount_discount = fields.Float(
        string='Desconto (-)',
        digits=dp.get_precision('Account'), store=True,
        help="The discount amount.")
    discount_rate = fields.Float(
        'Desconto', readonly=True, states={'draft': [('readonly', False)]})

    @api.onchange('discount_rate')
    def onchange_discount_rate(self):
        for sale_order in self:
            for sale_line in sale_order.order_line:
                sale_line.discount = sale_order.discount_rate


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    def _calc_line_base_price(self):
        return self.price_unit * (1 - (self.discount or 0.0) / 100.0)

    def _calc_line_quantity(self):
        return self.product_uom_qty

    def _calc_price_gross(self, qty):
        return self.price_unit * qty

    @api.one
    @api.depends('price_unit', 'tax_id', 'discount', 'product_uom_qty')
    def _amount_line(self):
        price = self._calc_line_base_price()
        qty = self._calc_line_quantity()
        self.price_gross = self._calc_price_gross(qty)
        self.discount_value = self.order_id.pricelist_id.currency_id.round(
            self.price_gross - (price * qty))

    fiscal_position_id = fields.Many2one(
        'account.fiscal.position', 'Fiscal Position',
        readonly=True, states={'draft': [('readonly', False)],
                               'sent': [('readonly', False)]})
    insurance_value = fields.Float('Insurance',
                                   default=0.0,
                                   digits=dp.get_precision('Account'))
    other_costs_value = fields.Float('Other costs',
                                     default=0.0,
                                     digits=dp.get_precision('Account'))
    freight_value = fields.Float('Freight',
                                 default=0.0,
                                 digits=dp.get_precision('Account'))

    discount_value = fields.Float(compute='_amount_line',
                                  string='Vlr. Desc. (-)', store=True,
                                  digits=dp.get_precision('Sale Price'))
    price_gross = fields.Float(
        compute='_amount_line', string='Vlr. Bruto', store=True,
        digits=dp.get_precision('Sale Price'))

    @api.multi
    def _prepare_invoice_line(self, qty):
        res = super(SaleOrderLine, self)._prepare_invoice_line(qty)

        res['insurance_value'] = self.insurance_value
        res['other_costs_value'] = self.other_costs_value
        res['freight_value'] = self.freight_value
        icms = self.tax_id.filtered(lambda x: x.domain == 'icms')
        if len(icms) > 1:
            raise UserError(
                'Apenas um imposto com o domínio ICMS deve ser cadastrado')
        res['tax_icms_id'] = icms and icms.id or False

        return res
