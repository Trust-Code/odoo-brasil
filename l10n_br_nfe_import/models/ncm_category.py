from odoo import fields, models


class NcmCategory(models.Model):
    _name = 'l10n_br.ncm.category'
    _description = "Categoria de NCM para importar"

    name = fields.Char(string="Código")
