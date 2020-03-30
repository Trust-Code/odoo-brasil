from odoo import fields, models


class ProductCategory(models.Model):
    _inherit = 'product.category'

    l10n_br_fiscal_category_id = fields.Many2one(
        'product.fiscal.category', string="Categoria Fiscal")

    l10n_br_ncm_category_ids = fields.Many2many(
        'l10n_br.ncm.category', string='Categorias NCM')
