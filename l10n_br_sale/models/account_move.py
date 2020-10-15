from odoo import fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    carrier_partner_id = fields.Many2one('res.partner', string='Transportadora')
