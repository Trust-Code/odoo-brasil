from odoo import api, fields, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    l10n_br_tax_rule_id = fields.Many2one(
        "account.fiscal.position.tax.rule", string="Regra Imposto"
    )

    l10n_br_calculated_taxes = fields.Text(string="Impostos Calculados")

    l10n_br_payment_value = fields.Monetary(
        string="Valor",
        compute="_compute_payment_value",
        currency_field="company_currency_id",
    )

    @api.depends(
        "debit", "credit", "account_id.internal_type", "amount_residual"
    )
    def _compute_payment_value(self):
        for item in self:
            item.l10n_br_payment_value = (
                item.debit
                if item.account_id.internal_type == "receivable"
                else item.credit * -1
            )

    def _get_computed_taxes(self):
        tax_ids = super(AccountMoveLine, self)._get_computed_taxes()
        if not self.move_id.fiscal_position_id:
            return tax_ids

        return tax_ids | self.move_id.fiscal_position_id.apply_tax_ids

    def action_register_payment_move_line(self):
        dummy, act_id = self.env['ir.model.data'].get_object_reference(
            'l10n_br_account', 'action_payment_account_move_line'
        )
        receivable = (self.account_id.internal_type == 'receivable')
        vals = self.env['ir.actions.act_window'].browse(act_id).read()[0]
        vals['context'] = {
            'default_amount': self.debit or self.credit,
            'default_partner_type': 'customer' if receivable else 'supplier',
            'default_partner_id': self.partner_id.id,
            'default_communication': self.name,
            'default_move_line_id': self.id,
        }
        return vals
