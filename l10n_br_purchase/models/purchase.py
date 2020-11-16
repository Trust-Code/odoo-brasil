from odoo import models, api


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    @api.onchange('fiscal_position_id', 'order_line')
    def _compute_tax_id(self):
        super(PurchaseOrder, self)._compute_tax_id()
        for line in self.order_line:
            if self.fiscal_position_id.apply_tax_ids.ids not in line.taxes_id.ids:
                line.taxes_id = line.taxes_id + self.fiscal_position_id.apply_tax_ids
