# © 2016 Fábio Luna <fabiocluna@hotmail.com>, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class AccountInvoiceRefund(models.TransientModel):
    _inherit = 'account.invoice.refund'

    fiscal_position_id = fields.Many2one(
        'account.fiscal.position', string="Posição Fiscal")

    @api.multi
    def invoice_refund(self):
        context = dict(self._context or {})
        for inv in self.env['account.invoice'].browse(
                context.get('active_ids')):
            self.atualiza_fiscal_pos(inv)
        res = super(AccountInvoiceRefund, self).invoice_refund()

        return res

    def atualiza_fiscal_pos(self, invoice_id):
        fiscal_pos = self.fiscal_position_id
        invoice_id.write({
            'fiscal_position_id': fiscal_pos.id,
            'product_serie_id': fiscal_pos.product_serie_id.id,
            'product_document_id': fiscal_pos.product_document_id.id,
            'service_serie_id': fiscal_pos.service_serie_id.id,
            'service_document_id': fiscal_pos.service_document_id.id,
            'fiscal_observation_ids': [(
                6, False, [x.id for x in fiscal_pos.fiscal_observation_ids]
            )]
        })

        if self.fiscal_position_id:
            for item in invoice_id.invoice_line_ids:
                price_unit = item.price_unit
                item._onchange_product_id()
                item._br_account_onchange_product_id()
                item.write({'price_unit': price_unit})
                item._set_extimated_taxes(price_unit)
