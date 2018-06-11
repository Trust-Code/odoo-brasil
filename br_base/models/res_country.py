# © 2009  Renato Lima - Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import models, fields


class ResCountry(models.Model):
    _name = 'res.country'
    _inherit = ['res.country', 'br.localization.filtering']

    l10n_br_bc_code = fields.Char('BC Code', size=5, oldname="bc_code")
    l10n_br_ibge_code = fields.Char('IBGE Code', size=5, oldname="ibge_code")
    l10n_br_siscomex_code = fields.Char(
        'Siscomex Code', size=4, oldname="siscomex_code")


class ResCountryState(models.Model):
    _name = 'res.country.state'
    _inherit = ['res.country.state', 'br.localization.filtering']

    l10n_br_ibge_code = fields.Char('IBGE Code', size=2, oldname="ibge_code")
