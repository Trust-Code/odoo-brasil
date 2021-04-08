from odoo import models


class Product(models.Model):
    _inherit = 'product.product'

    _sql_constraints = [('default_code_unique', 'unique(default_code)',
                         'O produto deve ter referência interna única!\n'
                         'Por favor, utilize uma referência diferente para esse produto.')]