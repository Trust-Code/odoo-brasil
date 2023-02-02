from odoo import models, fields


class StockPackageType(models.Model):
    _inherit = "stock.package.type"

    package_weight = fields.Float(string="Peso da Embalagem")
