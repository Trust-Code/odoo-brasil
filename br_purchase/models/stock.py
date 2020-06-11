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

            return self.price_unit or self.product_id.standard_price

        return super(StockMove, self)._get_price_unit()
