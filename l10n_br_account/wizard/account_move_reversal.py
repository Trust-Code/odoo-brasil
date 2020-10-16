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
