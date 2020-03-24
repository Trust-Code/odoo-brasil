from datetime import datetime
from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    l10n_br_edoc_policy = fields.Selection(
        [('directly', 'Emitir agora'),
         ('after_payment', 'Emitir após pagamento'),
         ('manually', 'Manualmente')], string="Nota Eletrônica", default='directly')

    def action_create_eletronic_document(self):
        for move in self:
            self.env['eletronic.document'].create({
                'name': move.name,
                'company_id': move.company_id.id,
                'partner_id': move.partner_id.id,
                'move_id': move.id,
            })

    def action_post(self):
        res = super(AccountMove, self).action_post()
        moves = self.filtered(lambda x: x.l10n_br_edoc_policy == 'directly')
        moves.action_create_eletronic_document()
        return res
