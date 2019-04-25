# © 2017 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    payment_mode_id = fields.Many2one(
        string="Modo de pagamento",
        comodel_name = 'l10n_br.payment.mode')

    @api.multi
    def _prepare_invoice(self):
        vals = super(SaleOrder, self)._prepare_invoice()
        invoice_env = self.env['account.invoice']
        p_term = self.payment_term_id
        payment_vals = invoice_env.prepare_preview_payment(p_term)
        payment_vals = self._preview_payment_amount(payment_vals)
        if self.payment_mode_id:
            for v in payment_vals:
                v[2]['payment_mode_id'] = self.payment_mode_id.id
        vals['preview_payment_ids'] = payment_vals
        return vals

    def _get_amount(self):
        order_lines = self.order_line.filtered(lambda x: x.qty_to_invoice > 0)
        amount = 0
        for line in order_lines:
            # Desconta a retenção se houver
            ret_perc = sum([tx.amount for tx in line.tax_id if tx.amount < 0])
            amount += line.price_subtotal * (1 - (abs(ret_perc) / 100))
        return amount

    def _preview_payment_amount(self, payment_vals):
        balance = amount = self._get_amount()
        for line_vals in payment_vals:
            if 'payment_term_line_id' in line_vals[2]:
                pt_line = self.env['account.payment.term.line'].browse(
                    line_vals[2]['payment_term_line_id'])
            else:
                pt_line = False

            if pt_line and pt_line.value == 'percent':
                mnt = round(amount * (pt_line.value_amount / 100), 2)
            elif pt_line and pt_line.value == 'fixed':
                mnt = pt_line.value_amount
            elif not pt_line or pt_line.value == 'balance':
                mnt = balance
            line_vals[2]['amount'] = mnt
            balance -= mnt
        return payment_vals


class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = "sale.advance.payment.inv"

    @api.multi
    def _create_invoice(self, order, so_line, amount):
        res = super(SaleAdvancePaymentInv, self)._create_invoice(
            order, so_line, amount)
        res._onchange_payment_term()
        # Corrige o modo de pagamento
        if order.payment_mode_id:
            p_mode = order.payment_mode_id.id
            preview_vals = []
            for line in res.preview_payment_ids:
                preview_vals.append((1, line.id, {'payment_mode_id': p_mode}))
            res.write({'preview_payment_ids': preview_vals})
        return res
