from odoo import fields, models


class NcmCategory(models.Model):
    _name = 'l10n_br.ncm.category'

    name = fields.Char(string="Código")
