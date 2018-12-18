# © 2018 Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    l10n_br_pymt_interest_account_id = fields.Many2one(
        'account.account',
        related='company_id.l10n_br_pymt_interest_account_id',
        string="Conta para pagamento de juros",
        domain="[('company_id', '=', company_id),\
                 ('user_type_id.type', '=', 'payable')]",
        help='Conta onde será debitado o montante dos juros pagos'
    )

    l10n_br_pymt_fine_account_id = fields.Many2one(
        'account.account',
        related='company_id.l10n_br_pymt_fine_account_id',
        string="Conta para pagamento de multa",
        help='Conta onde será debitado o montante das multas pagas'
    )

    l10n_br_interest_account_id = fields.Many2one(
        'account.account',
        related='company_id.l10n_br_interest_account_id',
        string="Conta para recebimento de juros",
        help='Conta onde será creditado o montante dos juros recebidos'
    )
    l10n_br_bankfee_account_id = fields.Many2one(
        'account.account',
        related='company_id.l10n_br_bankfee_account_id',
        string="Conta para tarifas bancárias",
        help='Conta onde será debitado o montante de tarifas pagas'
    )
