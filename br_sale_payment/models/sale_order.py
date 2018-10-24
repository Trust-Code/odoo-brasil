# -*- coding: utf-8 -*-
# © 2017 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    payment_mode_id = fields.Many2one(
        'l10n_br.payment.mode', string=u"Modo de pagamento")

    @api.multi
    def _prepare_invoice(self):
        vals = super(SaleOrder, self)._prepare_invoice()
        vals['payment_mode_id'] = self.payment_mode_id.id
        return vals
