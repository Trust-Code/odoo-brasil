from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    l10n_br_legal_name = fields.Char('Legal Name', size=60)
    l10n_br_cnpj_cpf = fields.Char('CNPJ/CPF', size=20)