from odoo import models, fields


class ProductPackaging(models.Model):
    _inherit = "product.packaging"

    package_carrier_type = fields.Selection(
        selection_add=[("correios", "Correios")]
    )
