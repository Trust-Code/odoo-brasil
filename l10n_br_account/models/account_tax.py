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

    def compute_all(self, price_unit, currency=None, quantity=1.0, product=None, partner=None, is_refund=False, handle_price_include=True, include_caba_tags=False):
        res = super(AccountTax, self).compute_all(
            price_unit,
            currency,
            quantity,
            product,
            partner,
            is_refund,
            handle_price_include,
            include_caba_tags,
        )

        retention_taxes = list(filter(lambda x: x["amount"] < 0, res["taxes"]))
        amount_retention = 0

        for tax in retention_taxes:
            tax["base"] += tax["amount"]
            amount_retention += tax["amount"]

        res["total_excluded"] += amount_retention
        res["total_void"] += amount_retention
        return res
