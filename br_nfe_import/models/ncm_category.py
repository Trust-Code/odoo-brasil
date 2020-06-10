# © 2018 Danimar Ribeiro <danimaribeiro@gmail.com>, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class NcmCategory(models.Model):
    _name = 'l10n_br.ncm.category'

    name = fields.Char(string="Código")
