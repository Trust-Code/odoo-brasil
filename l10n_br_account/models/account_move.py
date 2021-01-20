from odoo import api, fields, models


STATES = {"draft": [("readonly", False)]}


def compute_partition_amount(amount, line_amount, total_amount):
    if total_amount > 0:
        return round(amount * line_amount / total_amount, 2)
    return 0


class AccountMove(models.Model):
    _inherit = "account.move"

    l10n_br_delivery_amount = fields.Monetary(
        string="Frete",
        compute="_compute_l10n_br_delivery_amount",
        inverse="_inverse_l10n_br_delivery_amount",
        readonly=True,
        states=STATES,
    )
    l10n_br_expense_amount = fields.Monetary(
        string="Despesa",
        compute="_compute_l10n_br_expense_amount",
        inverse="_inverse_l10n_br_expense_amount",
        readonly=True,
        states=STATES,
    )
    l10n_br_insurance_amount = fields.Monetary(
        string="Seguro",
        compute="_compute_l10n_br_insurance_amount",
        inverse="_inverse_l10n_br_insurance_amount",
        readonly=True,
        states=STATES,
    )

    def _mapping_fiscal_position_account(self):
        if not self.fiscal_position_id:
            return

        fiscal_position_id = self.fiscal_position_id
        if fiscal_position_id.journal_id:
            self.journal_id = fiscal_position_id.journal_id

        if fiscal_position_id.account_id:
            account_id = fiscal_position_id.account_id
            move_lines = []

            if self.is_sale_document(include_receipts=True):
                move_lines = self.mapped("line_ids").filtered(
                    lambda x: x.account_id.user_type_id.type == "receivable"
                )
            elif self.is_purchase_document(include_receipts=True):
                move_lines = self.mapped("line_ids").filtered(
                    lambda x: x.account_id.user_type_id.type == "payable"
                )

            for line in move_lines:
                line.account_id = account_id

    def _unmap_lines(self):
        if not self.fiscal_position_id:
            return

        fiscal_position_id = self.fiscal_position_id

        if fiscal_position_id.account_id:
            if self.is_sale_document(include_receipts=True):
                self.mapped("line_ids").filtered(
                    lambda x: x.account_id == fiscal_position_id.account_id
                ).account_id = self.partner_id.property_account_payable_id
            elif self.is_purchase_document(include_receipts=True):
                self.mapped("line_ids").filtered(
                    lambda x: x.account_id == fiscal_position_id.account_id
                ).account_id = self.partner_id.property_account_receivable_id

    def _recompute_payment_terms_lines(self):
        self._unmap_lines()
        super(AccountMove, self)._recompute_payment_terms_lines()
        self._mapping_fiscal_position_account()

    @api.onchange("fiscal_position_id")
    def _onchange_fiscal_position_id(self):
        self._mapping_fiscal_position_account()

    def compute_lines_partition(self, line_type):
        if line_type not in ("delivery", "expense", "insurance"):
            return
        total = sum(
            line.price_unit * line.quantity
            for line in self.invoice_line_ids
            if not line.is_delivery_expense_or_insurance()
        )
        for line in self.invoice_line_ids.filtered(
            lambda x: not x.is_delivery_expense_or_insurance()
        ):
            field_name = "l10n_br_{}_amount".format(line_type)
            line.update(
                {
                    field_name: compute_partition_amount(
                        self[field_name],
                        line.price_unit * line.quantity,
                        total,
                    )
                }
            )

    def handle_delivery_expense_insurance_lines(self, line_type):
        if line_type not in ("delivery", "expense", "insurance"):
            return
        boolean_field_name = "l10n_br_is_{}".format(line_type)
        amount_field_name = "l10n_br_{}_amount".format(line_type)
        line = self.invoice_line_ids.filtered(lambda x: x[boolean_field_name])
        if line and self[amount_field_name] > 0:
            line.update(
                {
                    "price_unit": self[amount_field_name],
                    "quantity": 1,
                }
            )
        elif line:
            line.unlink()
        elif self[amount_field_name] > 0:
            product_external_id = "l10n_br_account.product_product_{}".format(
                line_type
            )
            product = self.env.ref(product_external_id)
            self.update(
                {
                    "invoice_line_ids": [
                        (
                            0,
                            0,
                            {
                                "move_id": self.id,
                                "product_id": product.id,
                                "name": product.name_get()[0][1],
                                "price_unit": self[amount_field_name],
                                "quantity": 1,
                                boolean_field_name: True,
                            },
                        )
                    ]
                }
            )
        self.compute_lines_partition(line_type)
        self.with_context(
            check_move_validity=False
        )._move_autocomplete_invoice_lines_values()

    @api.onchange(
        "invoice_line_ids",
        "invoice_line_ids.price_unit",
        "invoice_line_ids.quantity",
    )
    def _compute_l10n_br_delivery_amount(self):
        for item in self:
            delivery_line = item.invoice_line_ids.filtered(
                lambda x: x.l10n_br_is_delivery
            )
            item.l10n_br_delivery_amount = delivery_line.price_total
            item.compute_lines_partition("delivery")

    def _inverse_l10n_br_delivery_amount(self):
        for item in self:
            item.handle_delivery_expense_insurance_lines("delivery")

    @api.onchange(
        "invoice_line_ids",
        "invoice_line_ids.price_unit",
        "invoice_line_ids.quantity",
    )
    def _compute_l10n_br_expense_amount(self):
        for item in self:
            expense_line = item.invoice_line_ids.filtered(
                lambda x: x.l10n_br_is_expense
            )
            item.l10n_br_expense_amount = expense_line.price_total
            item.compute_lines_partition("expense")

    def _inverse_l10n_br_expense_amount(self):
        for item in self:
            item.handle_delivery_expense_insurance_lines("expense")

    @api.onchange(
        "invoice_line_ids",
        "invoice_line_ids.price_unit",
        "invoice_line_ids.quantity",
    )
    def _compute_l10n_br_insurance_amount(self):
        for item in self:
            insurance_line = item.invoice_line_ids.filtered(
                lambda x: x.l10n_br_is_insurance
            )
            item.l10n_br_insurance_amount = insurance_line.price_total
            item.compute_lines_partition("insurance")

    def _inverse_l10n_br_insurance_amount(self):
        for item in self:
            item.handle_delivery_expense_insurance_lines("insurance")


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    l10n_br_calculated_taxes = fields.Text(string="Impostos Calculados")

    l10n_br_payment_value = fields.Monetary(
        string="Valor",
        compute="_compute_payment_value",
        currency_field="company_currency_id",
    )

    l10n_br_is_delivery = fields.Boolean(string="É Entrega?")
    l10n_br_is_expense = fields.Boolean(string="É Despesa?")
    l10n_br_is_insurance = fields.Boolean(string="É Seguro?")

    l10n_br_delivery_amount = fields.Monetary(string="Frete")
    l10n_br_expense_amount = fields.Monetary(string="Despesa")
    l10n_br_insurance_amount = fields.Monetary(string="Seguro")

    def is_delivery_expense_or_insurance(self):
        return (
            self.l10n_br_is_delivery
            or self.l10n_br_is_expense
            or self.l10n_br_is_insurance
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
        dummy, act_id = self.env["ir.model.data"].get_object_reference(
            "l10n_br_account", "action_payment_account_move_line"
        )
        receivable = self.account_id.internal_type == "receivable"
        vals = self.env["ir.actions.act_window"].browse(act_id).read()[0]
        vals["context"] = {
            "default_amount": self.debit or self.credit,
            "default_partner_type": "customer" if receivable else "supplier",
            "default_partner_id": self.partner_id.id,
            "default_communication": self.name,
            "default_move_line_id": self.id,
        }
        return vals
