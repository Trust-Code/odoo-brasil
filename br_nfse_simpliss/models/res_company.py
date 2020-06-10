# © 2019 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    senha_nfse_simpliss = fields.Char(
        string='Senha NFSe SimplISS', size=30,
        help=u'Senha Nota Fiscal de Serviço')
