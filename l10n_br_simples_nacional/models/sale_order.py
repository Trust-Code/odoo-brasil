# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, models
from odoo.exceptions import UserError


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.multi
    def _prepare_invoice_line(self, qty):
        res = super(SaleOrderLine, self)._prepare_invoice_line(qty)

        icms = self.tax_id.filtered(lambda x: x.domain == 'simples')
        if len(icms) > 1:
            raise UserError(
                'Apenas um imposto com o domínio ICMS deve ser cadastrado')
        res['tax_icms_id'] = icms and icms.id or False

        return res
