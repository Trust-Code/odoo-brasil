from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    l10n_br_tax_regime = fields.Selection(
        [('simples', 'Simples Nacional'),
         ('presumido', 'Lucro Presumido'),
         ('real', 'Lucro Real')], string="Regime tributário")

    l10n_br_aedf = fields.Char(
        string="Número AEDF", size=10, help="Número de autorização para emissão de NFSe")
    l10n_br_client_id = fields.Char(string='Client Id', size=50)
    l10n_br_client_secret = fields.Char(string='Client Secret', size=50)
    l10n_br_user_password = fields.Char(string='Senha Acesso', size=50)