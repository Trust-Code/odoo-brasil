from odoo import models, fields


class ProductPackaging(models.Model):
    _inherit = "product.packaging"

    package_weight = fields.Float(string="Peso da Embalagem")
