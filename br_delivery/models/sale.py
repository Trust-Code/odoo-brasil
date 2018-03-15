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
        domain = [('sale_id', '=', self.id)]
        if all(item.invoice_policy == 'delivery' for item in
                self.order_line.product_id):
            domain.append(('state', '=', 'done'))
        pick = self.env['stock.picking'].search(
            domain)
        if pick:
            result.update({
                'carrier_id': pick[0].carrier_id.id,
                'incoterm': pick[0].incoterm.id,
                'shipping_supplier': pick[0].carrier_id.partner_id.id,
                'freight_responsibility': pick[0].freight_responsibility,
                'vehicle_plate': pick[0].vehicle_plate,
                'vehicle_state_id': pick[0].vehicle_state_id.id,
                'vehicle_rntc': pick[0].vehicle_rntc,
            })
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
