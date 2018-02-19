# © 2017 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class ResStateCity(models.Model):
    _inherit = 'res.state.city'

    siafi_code = fields.Char(u'Código SIAFI', size=10)
