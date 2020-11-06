from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    @api.onchange("fiscal_position_id")
    def _onchange_fiscal_position_id(self):
        if not self.fiscal_position_id:
            return

        fiscal_position_id = self.fiscal_position_id
        if fiscal_position_id.journal_id:
            self.journal_id = fiscal_position_id.journal_id

        if fiscal_position_id.account_id:
            account_id = fiscal_position_id.account_id

            if fiscal_position_id.fiscal_type == "saida":
                move_lines = self.mapped("line_ids").filtered(
                    lambda x: x.debit > 0
                )

                for line in move_lines:
                    line.account_id = account_id
            elif fiscal_position_id.fiscal_type == "entrada":
                move_lines = self.mapped("line_ids").filtered(
                    lambda x: x.credit > 0
                )

                for line in move_lines:
                    line.account_id = account_id


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

    @api.onchange("product_id")
    def _onchange_product_id(self):
        vals = super(AccountMoveLine, self)._onchange_product_id()

        if not self.move_id.fiscal_position_id:
            return vals

        fiscal_position_id = self.move_id.fiscal_position_id

        if fiscal_position_id.account_id:
            self.account_id = fiscal_position_id.account_id
