from odoo import models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def _compute_tax_id(self):
        super(SaleOrderLine, self)._compute_tax_id()

        for line in self:
            fiscal_position_id = line.order_id.fiscal_position_id

            if fiscal_position_id:
                line.tax_id = fiscal_position_id.apply_tax_ids
