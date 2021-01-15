from odoo import models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _prepare_invoice(self):
        values = super(SaleOrder, self)._prepare_invoice()

        if self.carrier_id and self.carrier_id.partner_id:
            values['carrier_partner_id'] = self.carrier_id.partner_id
        return values


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def _compute_tax_id(self):
        super(SaleOrderLine, self)._compute_tax_id()

        for line in self:
            fiscal_position_id = line.order_id.fiscal_position_id

            if fiscal_position_id:
                line.tax_id += fiscal_position_id.apply_tax_ids
