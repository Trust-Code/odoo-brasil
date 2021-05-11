from odoo import fields, models


class AccountFiscalPosition(models.Model):
    _inherit = 'account.fiscal.position'

    l10n_br_cfop_id = fields.Many2one(
        'nfe.cfop', string="CFOP",
        help="CFOP da nota fiscal.", copy=True)

    fiscal_observation_ids = fields.Many2many(
        'nfe.fiscal.observation', string=u"Mensagens Doc. Eletrônico",
        copy=True)
