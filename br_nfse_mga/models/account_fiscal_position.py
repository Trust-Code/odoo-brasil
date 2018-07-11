from odoo import models, fields


class AccountFiscalPosition(models.Model):
    _inherit = "account.fiscal.position"

    exigibilidade_iss = fields.Selection(
        [('1', 'Exigível'), ('2', 'Não incidência'),
         ('3', 'Isenção'), ('4', 'Exportação'),
         ('5', 'Imunidade'),
         ('6', 'Exigibilidade Suspensa por Decisão Judicial'),
         ('7', 'Exigibilidade Suspensa por Processo Administrativo')],
        string="Exigibilidade ISS")
