
from odoo import api, fields, models


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
    l10n_br_retention = fields.Boolean(string="Retenção?", compute="_compute_retention", inverse="_inverse_retention")

    def compute_all(self, price_unit, currency=None, quantity=1.0, product=None, partner=None, is_refund=False, handle_price_include=True):
        taxes = super(AccountTax, self).compute_all(
            price_unit, currency, quantity, product, partner,
            is_refund, handle_price_include)

        return taxes

    @api.depends("amount")
    def _compute_retention(self):
        if self.amount < 0:
            self.l10n_br_retention = True
        else:
            self.l10n_br_retention = False

    def _inverse_retention(self):
        self.l10n_br_retention = self.l10n_br_retention

    @api.onchange("l10n_br_retention")
    def _onchange_retention(self):
        if (self.l10n_br_retention and self.amount > 0 or 
            not self.l10n_br_retention and self.amount < 0):
            self.amount = self.amount * (-1)
