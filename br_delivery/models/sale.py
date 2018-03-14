# -*- coding: utf-8 -*-
# © 2009  Renato Lima - Akretion
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.multi
    def _prepare_invoice(self):
        result = super(SaleOrder, self)._prepare_invoice()
        if self.carrier_id:
            result['carrier_id'] = self.carrier_id.id
            result['incoterm'] = self.incoterm.id
            result['freight_responsibility'] =\
                self.incoterm.freight_responsibility
        return result

    def get_delivery_price(self):
        super(SaleOrder, self).get_delivery_price()
        self.total_frete = self.delivery_price
        self._amount_all()
        self._onchange_despesas_frete_seguro()

    @api.onchange('carrier_id')
    def onchange_carrier_id(self):
        if self.carrier_id:
            self.incoterm = self.carrier_id.incoterm
