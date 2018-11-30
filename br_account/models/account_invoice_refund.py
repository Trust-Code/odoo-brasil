# -*- coding: utf-8 -*-
# © 2016 Fábio Luna <fabiocluna@hotmail.com>, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class AccountInvoiceRefund(models.TransientModel):
    _inherit = 'account.invoice.refund'

    fiscal_position_id = fields.Many2one(
        'account.fiscal.position', string="Posição Fiscal")

    @api.multi
    def invoice_refund(self):
        res = super(AccountInvoiceRefund, self).invoice_refund()
        if type(res) is bool:
            return res
        if "domain" not in res:
            return res

        invoice_id = res['domain'][1][2][0]
        invoice_id = self.env['account.invoice'].search([
            ('id', '=', invoice_id)
        ])

        invoice_id.write({'fiscal_position_id': self.fiscal_position_id.id})

        if self.fiscal_position_id:
            for item in invoice_id.invoice_line_ids:
                price_unit = item.price_unit
                item._onchange_product_id()
                item._br_account_onchange_product_id()
                item.write({'price_unit': price_unit})
                item._set_extimated_taxes(price_unit)

        return res
