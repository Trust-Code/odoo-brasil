from odoo import fields, models


class City(models.Model):
    _inherit = 'res.city'

    l10n_br_ibge_code = fields.Char('IBGE Code', size=10)
