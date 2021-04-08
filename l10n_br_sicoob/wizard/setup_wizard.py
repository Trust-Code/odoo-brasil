from odoo import models, fields


class SetupBarBankConfigWizard(models.TransientModel):
    _inherit = 'account.setup.bank.manual.config'

    l10n_br_bank_branch_number = fields.Char(string='Número da Agência')
