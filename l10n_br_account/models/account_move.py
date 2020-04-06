from odoo import api, fields, models


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    l10n_br_tax_rule_id = fields.Many2one(
        'account.fiscal.position.tax.rule', string='Regra Imposto')

    l10n_br_calculated_taxes = fields.Text(string='Impostos Calculados')

    def _get_computed_taxes(self):
        tax_ids = super(AccountMoveLine, self)._get_computed_taxes()
        if not self.move_id.fiscal_position_id:
            return tax_ids

        return tax_ids | self.move_id.fiscal_position_id.apply_tax_ids