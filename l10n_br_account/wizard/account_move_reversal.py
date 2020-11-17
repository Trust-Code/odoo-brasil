from odoo import models, fields


class AccountMoveReversal(models.TransientModel):
    _inherit = 'account.move.reversal'

    fiscal_position_id = fields.Many2one(
        'account.fiscal.position', string='Posição Fiscal')

    def _prepare_default_reversal(self, move):
        vals = super(AccountMoveReversal, self)._prepare_default_reversal(move)

        if self.fiscal_position_id:
            vals['fiscal_position_id'] = self.fiscal_position_id.id

        return vals

    def reverse_moves(self):
        res = super(AccountMoveReversal, self).reverse_moves()

        if 'res_id' in res:
            invoice_ids = self.env['account.move'].browse(res.get('res_id'))
        else:
            invoice_ids = self.env['account.move'].search(res.get('domain'))

        fiscal_pos = self.fiscal_position_id
        for invoice_id in invoice_ids:
            for line in invoice_id.invoice_line_ids:
                if line.move_id.state == 'draft':
                    line.tax_ids = fiscal_pos.apply_tax_ids

        return res
