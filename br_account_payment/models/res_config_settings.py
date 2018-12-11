# © 2018 Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


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

    l10n_br_fine_account_id = fields.Many2one(
        'account.account',
        related='company_id.l10n_br_fine_account_id',
        string="Conta para recebimento de multa",
        help='Conta onde será creditado o montante das multas recebidas'
    )

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        params = self.env['ir.config_parameter'].sudo()
        res.update(
            l10n_br_interest_account_id=int(params.get_param(
                'br_payment_cnab.l10n_br_interest_account_id', default=0)),
            l10n_br_fine_account_id=int(params.get_param(
                'br_payment_cnab.l10n_br_fine_account_id', default=0)),
            l10n_br_pymt_interest_account_id=int(params.get_param(
                'br_payment_cnab.l10n_br_pymt_interest_account_id',
                default=0)),
            l10n_br_pymt_fine_account_id=int(params.get_param(
                'br_payment_cnab.l10n_br_pymt_fine_account_id', default=0))
        )
        return res

    @api.multi
    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param(
            'br_payment_cnab.l10n_br_interest_account_id',
            self.l10n_br_interest_account_id.id)
        self.env['ir.config_parameter'].sudo().set_param(
            'br_payment_cnab.l10n_br_fine_account_id',
            self.l10n_br_fine_account_id.id)
        self.env['ir.config_parameter'].sudo().set_param(
            'br_payment_cnab.l10n_br_pymt_interest_account_id',
            self.l10n_br_pymt_interest_account_id.id)
        self.env['ir.config_parameter'].sudo().set_param(
            'br_payment_cnab.l10n_br_pymt_fine_account_id',
            self.l10n_br_pymt_fine_account_id.id)
