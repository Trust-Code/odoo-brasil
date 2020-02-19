from odoo import models, fields


class ResCountry(models.Model):
    _inherit = 'res.country'

    l10n_br_ibge_code = fields.Char('Código IBGE', size=10)


class ResCountryState(models.Model):
    _inherit = 'res.country.state'

    l10n_br_ibge_code = fields.Char('Código IBGE', size=10)
