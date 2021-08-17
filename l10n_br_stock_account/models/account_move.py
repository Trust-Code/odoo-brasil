from odoo import fields, models

class AccountMove(models.Model):
    _inherit = "account.move"

    l10n_br_picking_origin_id = fields.Many2one(string="Stock Picking", comodel_name="stock.picking")
