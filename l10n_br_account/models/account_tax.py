from odoo import fields, models


class AccountTax(models.Model):
    _inherit = 'account.tax'

    domain = fields.Selection([('icms', 'ICMS'),
                               ('icmsst', 'ICMS ST'),
                               ('pis', 'PIS'),
                               ('cofins', 'COFINS'),
                               ('ipi', 'IPI'),
                               ('iss', 'ISS'),
                               ('ii', 'II'),
                               ('icms_inter', 'Difal - Alíquota Inter'),
                               ('icms_intra', 'Difal - Alíquota Intra'),
                               ('fcp', 'FCP'),
                               ('irpj', 'IRPJ'),
                               ('csll', 'CSLL'),
                               ('irrf', 'IRRF'),
                               ('inss', 'INSS'),
                               ('outros', 'Outros')], string="Tipo")


