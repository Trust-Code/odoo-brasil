from odoo import fields, models, api


class AccountMove(models.Model):
    _inherit = 'account.move'

    nfe_number = fields.Integer(
        string=u"Número NFe", compute="_compute_nfe_number")

    def _compute_nfe_number(self):
        for item in self:
            docs = self.env['eletronic.document'].search(
                [('move_id', '=', item.id)])
            if docs:
                item.nfe_number = docs[0].numero
            else:
                item.nfe_number = 0
