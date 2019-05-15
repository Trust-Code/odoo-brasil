# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    senha_nfse_imperial = fields.Char(
        string="Senha NFSe - Imperial", size=70)
    iss_simples_nacional = fields.Float(string="ISS Simples Nacional")
