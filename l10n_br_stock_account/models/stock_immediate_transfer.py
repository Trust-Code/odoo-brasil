# © 2021 - Fábio Luna - Code 137

from odoo import models


class StockImmediateTransfer(models.TransientModel):
    _inherit = "stock.immediate.transfer"

    def process(self):
        res = super(StockImmediateTransfer, self).process()
        pickings_to_validate = self.env['stock.picking'].browse(self.env.context.get('button_validate_picking_ids'))
        pickings_to_validate.action_invoice_picking()
        return res
