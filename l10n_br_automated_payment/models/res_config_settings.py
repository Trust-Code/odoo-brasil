from odoo import models, fields


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    l10n_br_payment_interest_account_id = fields.Many2one(
        'account.account',
        string="Conta para pagamento de juros/multa",
        help='Conta onde será registrado o montante dos juros e multas pagos'
    )
    l10n_br_payment_discount_account_id = fields.Many2one(
        'account.account',
        string="Conta para desconto de pagamentos",
        help='Conta onde será registrado o desconto recebido de pagamentos'
    )

    l10n_br_interest_account_id = fields.Many2one(
        'account.account',
        string="Conta para recebimento de juros",
        help='Conta onde será creditado o montante dos juros recebidos'
    )
    l10n_br_bankfee_account_id = fields.Many2one(
        'account.account',
        string="Conta para tarifas bancárias",
        help='Conta onde será debitado o montante de tarifas pagas'
    )

    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        res['l10n_br_payment_interest_account_id'] = self.env.user.company_id.l10n_br_payment_interest_account_id.id
        res['l10n_br_payment_discount_account_id'] = self.env.user.company_id.l10n_br_payment_discount_account_id.id
        res['l10n_br_interest_account_id'] = self.env.user.company_id.l10n_br_interest_account_id.id
        res['l10n_br_bankfee_account_id'] = self.env.user.company_id.l10n_br_bankfee_account_id.id
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env.user.company_id.l10n_br_payment_interest_account_id = self.l10n_br_payment_interest_account_id
        self.env.user.company_id.l10n_br_payment_discount_account_id = self.l10n_br_payment_discount_account_id
        self.env.user.company_id.l10n_br_interest_account_id = self.l10n_br_interest_account_id
        self.env.user.company_id.l10n_br_bankfee_account_id = self.l10n_br_bankfee_account_id