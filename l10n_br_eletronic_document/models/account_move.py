from datetime import datetime
from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    def action_post(self):
        res = super(AccountMove, self).action_post()
        for move in self.filtered(lambda x: x.type == 'out_invoice'):
            doc = self.env['eletronic.document'].create({
                'name': move.name,
                'emission_date': datetime.now(),
                'company_id': move.company_id.id,
                'partner_id': move.partner_id.id,
            })
            doc.generate()


