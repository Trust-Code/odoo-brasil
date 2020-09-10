from odoo import models, fields


class ChooseDeliveryCarrier(models.TransientModel):
    _inherit = "choose.delivery.carrier"

    packaging_id = fields.Many2one(
        comodel_name="product.packaging", string="Packages"
    )

    def _get_shipment_rate(self):
        return super(
            ChooseDeliveryCarrier,
            self.with_context(default_packaging_id=self.packaging_id.id),
        )._get_shipment_rate()
