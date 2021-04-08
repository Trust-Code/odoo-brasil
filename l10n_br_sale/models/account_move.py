from odoo import fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    carrier_partner_id = fields.Many2one('res.partner', string='Transportadora')
    num_volumes = fields.Integer('Quant. total de volumes')
    quant_peso = fields.Float('Peso')
    # peso_uom = fields.Many2one('uom.uom')

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