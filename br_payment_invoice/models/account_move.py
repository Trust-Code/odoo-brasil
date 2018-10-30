

from odoo import models


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    def open_wizard_schedule_payment(self):
        line = self.env['payment.order.line'].search([
            ('move_line_id', '=', self.id)
        ])
        return({
            'name': 'Alterar Dados Pagamento',
            'type': 'ir.actions.act_window',
            'res_model': 'wizard.change.payment',
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_move_line_id': self.id,
                'default_payment_mode_id': self.payment_mode_id.id,
                'default_bank_account_id':
                self.invoice_id.l10n_br_bank_account_id.id,
                'default_barcode': line.payment_information_id.barcode or '',
            }
        })
