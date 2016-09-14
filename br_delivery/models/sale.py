# -*- coding: utf-8 -*-
# © 2009  Renato Lima - Akretion
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api,  models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.multi
    def _prepare_invoice(self):
        result = super(SaleOrder, self)._prepare_invoice()
        if self.carrier_id:
            result['carrier_id'] = self.carrier_id.id
        return result
