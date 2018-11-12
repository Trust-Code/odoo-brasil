# © 2018 Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models
from odoo.exceptions import UserError


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    l10n_br_payment_type = fields.Selection(
        related="payment_mode_id.payment_type")
    l10n_br_bank_account_id = fields.Many2one(
        'res.partner.bank', string="Conta p/ Transferência",
        domain="[('partner_id', '=', partner_id)]")

    def prepare_payment_line_vals(self, move_line_id):
        return {
            'partner_id': self.partner_id.id,
            'amount_total': abs(move_line_id.amount_residual),
            'name': self.number,
            'bank_account_id': self.l10n_br_bank_account_id.id,
            'partner_acc_number': self.l10n_br_bank_account_id.acc_number,
            'partner_bra_number': self.l10n_br_bank_account_id.bra_number,
            'move_line_id': move_line_id.id,
            'date_maturity': move_line_id.date_maturity,
            'invoice_date': move_line_id.date,
            'invoice_id': self.id,
        }

    def check_create_payment_line(self):
        if self.payment_mode_id.type != 'payable':
            return
        if self.l10n_br_payment_type in ('03'):  # Boletos
            return
        elif self.l10n_br_payment_type in ('01', '02'):  # Depósitos
            if not self.l10n_br_bank_account_id:
                raise UserError('A conta bancária para depósito é obrigatório')
        else:
            raise UserError('Para tributos utilize os recibos de compra')

        for item in self.payable_move_line_ids:
            if not item.payment_mode_id:
                return
            vals = self.prepare_payment_line_vals(item)
            line_obj = self.env['payment.order.line'].with_context({})
            line_obj.action_generate_payment_order_line(
                item.payment_mode_id, vals)

    @api.multi
    def action_move_create(self):
        super(AccountInvoice, self).action_move_create()
        for item in self:
            item.check_create_payment_line()
