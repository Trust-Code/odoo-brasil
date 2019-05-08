# -*- coding: utf-8 -*-
# © 2018 Mackilem Van der Laan, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, models


class StockMove(models.Model):
    _inherit = 'stock.move'

    @api.multi
    def _get_price_unit(self):
        self.ensure_one()
        if self.purchase_line_id \
                and self.product_id.id == self.purchase_line_id.product_id.id:
            line = self.purchase_line_id
            order = line.order_id
            ctx = line._prepare_tax_context()
            tax_ids = line.taxes_id.with_context(**ctx)
            price = line.price_unit
            if line.taxes_id:
                taxes = tax_ids.compute_all(
                    price,
                    currency=line.order_id.currency_id,
                    quantity=1.0,
                    product=self.product_id,
                    partner=line.order_id.partner_id)

                price = taxes['total_included']
                for tax in taxes['taxes']:
                    if tax['account_id']:
                        price -= tax['amount']
            if self.product_uom.id != self.product_id.uom_id.id:
                price *= self.product_uom.factor/self.product_id.uom_id.factor
            if order.currency_id != order.company_id.currency_id:
                price = order.currency_id.compute(price,
                                                  order.company_id.currency_id,
                                                  round=False)
            return price
        return super(StockMove, self)._get_price_unit()
