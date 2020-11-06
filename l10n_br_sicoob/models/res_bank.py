from odoo import models, fields


class ResBank(models.Model):
    _inherit = 'res.partner.bank'

    l10n_br_branch_number = fields.Char("Agência Bancária")
