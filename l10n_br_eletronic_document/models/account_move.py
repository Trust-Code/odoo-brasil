from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    def action_post(self):
        res = super(AccountMove, self).action_post()
        for move in self:
            doc = self.env['eletronic.document'].create({'name': move.name})
            doc.generate()


