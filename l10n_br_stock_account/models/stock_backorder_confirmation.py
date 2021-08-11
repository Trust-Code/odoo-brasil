# © 2021 - Fábio Luna - Code 137

from odoo import models


class StockBackorderConfirmation(models.TransientModel):
    _inherit = "stock.backorder.confirmation"

    """Verificar as quantidades dos produtos na invoice após sua criação"""

    def process(self):
        res = super(StockBackorderConfirmation, self).process()
        pickings_to_validate = self.env['stock.picking'].browse(self.env.context.get('button_validate_picking_ids'))
        pickings_to_validate.action_invoice_picking()
        return res

    def process_cancel_backorder(self):
        res = super(StockBackorderConfirmation,
                    self).process_cancel_backorder()
        pickings_to_validate = self.env['stock.picking'].browse(self.env.context.get('button_validate_picking_ids'))
        pickings_to_validate.action_invoice_picking()
        return res
