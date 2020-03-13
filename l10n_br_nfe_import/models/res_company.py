from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    product_sequence_id = fields.Many2one(
        'ir.sequence', string="Sequência para código de produto")
