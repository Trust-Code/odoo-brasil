# © 2018 Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    l10n_br_payment_interest_account_id = fields.Many2one(
        'account.account',
        string="Conta para pagamento de juros/multa",
        help='Conta onde será registrado o montante dos juros e multas pagos',
        related='company_id.l10n_br_payment_interest_account_id',
        readonly=False
    )
    l10n_br_payment_discount_account_id = fields.Many2one(
        'account.account',
        string="Conta para desconto de pagamentos",
        help='Conta onde será registrado o desconto recebido de pagamentos',
        related='company_id.l10n_br_payment_discount_account_id',
        readonly=False
    )
    l10n_br_interest_account_id = fields.Many2one(
        'account.account',
        string="Conta para recebimento de juros",
        help='Conta onde será creditado o montante dos juros recebidos',
        related='company_id.l10n_br_interest_account_id',
        readonly=False
    )
    l10n_br_bankfee_account_id = fields.Many2one(
        'account.account',
        string="Conta para tarifas bancárias",
        help='Conta onde será debitado o montante de tarifas pagas',
        related='company_id.l10n_br_bankfee_account_id',
        readonly=False
    )
