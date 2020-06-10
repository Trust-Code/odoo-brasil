# © 2018 Danimar Ribeiro <danimaribeiro@gmail.com>, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class ProductCategory(models.Model):
    _inherit = 'product.category'

    l10n_br_fiscal_category_id = fields.Many2one(
        'br_account.fiscal.category', string="Categoria Fiscal")

    l10n_br_ncm_category_ids = fields.Many2many(
        'l10n_br.ncm.category', string='Categorias NCM')
