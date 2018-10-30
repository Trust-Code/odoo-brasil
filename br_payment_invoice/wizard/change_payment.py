

from odoo import fields, models
from odoo.exceptions import UserError


class WizardChangePayment(models.TransientModel):
    _name = 'wizard.change.payment'

    move_line_id = fields.Many2one('account.move.line', readonly=True)
    payment_mode_id = fields.Many2one(
        'l10n_br.payment.mode', string="Modo de Pagamento")
    payment_type = fields.Selection(
        related="payment_mode_id.payment_type")
    barcode = fields.Char(string="Código de barras")
    partner_id = fields.Many2one(
        'res.partner', readonly=True, string="Parceiro")
    bank_account_id = fields.Many2one(
        'res.partner.bank', string="Conta p/ Transferência",
        domain="[('partner_id', '=', partner_id)]")
    date_maturity = fields.Date(string="Data de Vencimento")

    def action_update_info(self):
        order_line = self.env['payment.order.line'].search(
            [('move_line_id', '=', self.move_line_id.id)])
        invoice = self.move_line_id.invoice_id
        if order_line and order_line.state == 'draft':
            order_line.write({
                'payment_mode_id': self.payment_mode_id.id,
                'barcode': self.barcode,
                'bank_account_id': self.bank_account_id.id,
                'date_maturity': self.date_maturity or order_line.date_maturity
            })
            self.move_line_id.write({
                'payment_mode_id': self.payment_mode_id.id,
                'date_maturity':
                self.date_maturity or self.move_line_id.date_maturity,
            })
        elif order_line:
            raise UserError(
                'O pagamento já foi processado! \
                Não é possível modificar informações aqui!')
        else:
            vals = invoice.prepare_payment_line_vals(self.move_line_id)
            vals['barcode'] = self.barcode
            vals['bank_account_id'] = self.bank_account_id.id
            self.env['payment.order.line'].action_generate_payment_order_line(
                self.payment_mode_id, **vals)
