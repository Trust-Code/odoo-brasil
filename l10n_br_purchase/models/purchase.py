from odoo import models, fields, api

STATES = {"draft": [("readonly", False)]}


def compute_partition_amount(amount, line_amount, total_amount):
    if total_amount > 0:
        return round(amount * line_amount / total_amount, 2)
    return 0


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

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

    def compute_lines_partition(self, line_type):
        if line_type not in ("delivery", "expense", "insurance"):
            return
        total = sum(
            line.price_unit * line.product_qty
            for line in self.order_line
            if not line.is_delivery_expense_or_insurance()
        )
        for line in self.order_line.filtered(
            lambda x: not x.is_delivery_expense_or_insurance()
        ):
            field_name = "l10n_br_{}_amount".format(line_type)
            line[field_name] = compute_partition_amount(
                self[field_name],
                line.price_unit * line.product_qty,
                total,
            )

    def handle_delivery_expense_insurance_lines(self, line_type):
        if line_type not in ("delivery", "expense", "insurance"):
            return
        boolean_field_name = "l10n_br_is_{}".format(line_type)
        amount_field_name = "l10n_br_{}_amount".format(line_type)
        line = self.order_line.filtered(lambda x: x[boolean_field_name])
        if line and self[amount_field_name] > 0:
            line.write(
                {
                    "price_unit": self[amount_field_name],
                    "product_qty": 1,
                }
            )
        elif line:
            line.unlink()
        elif self[amount_field_name] > 0:
            product_external_id = "l10n_br_account.product_product_{}".format(
                line_type
            )
            product = self.env.ref(product_external_id)
            self.write(
                {
                    "order_line": [
                        (
                            0,
                            0,
                            {
                                "order_id": self.id,
                                "product_id": product.id,
                                "name": product.name_get()[0][1],
                                "price_unit": self[amount_field_name],
                                "product_qty": 1,
                                boolean_field_name: True,
                                "date_planned": fields.Datetime.now(),
                                "product_uom": 1,
                            },
                        )
                    ]
                }
            )
        self.compute_lines_partition(line_type)
        for line in self.order_line.filtered(
            lambda x: not x.is_delivery_expense_or_insurance()
        ):
            line._compute_tax_id()

    @api.onchange(
        "order_line",
        "order_line.price_unit",
        "order_line.product_qty",
    )
    def _compute_l10n_br_delivery_amount(self):
        for item in self:
            delivery_line = item.order_line.filtered(
                lambda x: x.l10n_br_is_delivery
            )
            item.l10n_br_delivery_amount = delivery_line.price_total
            item.compute_lines_partition("delivery")

    def _inverse_l10n_br_delivery_amount(self):
        for item in self:
            item.handle_delivery_expense_insurance_lines("delivery")

    @api.onchange(
        "order_line",
        "order_line.price_unit",
        "order_line.product_qty",
    )
    def _compute_l10n_br_expense_amount(self):
        for item in self:
            expense_line = item.order_line.filtered(
                lambda x: x.l10n_br_is_expense
            )
            item.l10n_br_expense_amount = expense_line.price_total
            item.compute_lines_partition("expense")

    def _inverse_l10n_br_expense_amount(self):
        for item in self:
            item.handle_delivery_expense_insurance_lines("expense")

    @api.onchange(
        "order_line",
        "order_line.price_unit",
        "order_line.product_qty",
    )
    def _compute_l10n_br_insurance_amount(self):
        for item in self:
            insurance_line = item.order_line.filtered(
                lambda x: x.l10n_br_is_insurance
            )
            item.l10n_br_insurance_amount = insurance_line.price_total
            item.compute_lines_partition("insurance")

    def _inverse_l10n_br_insurance_amount(self):
        for item in self:
            item.handle_delivery_expense_insurance_lines("insurance")


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    l10n_br_is_delivery = fields.Boolean(string="É Frete?")
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

    def _compute_tax_id(self):
        super(PurchaseOrderLine, self)._compute_tax_id()
        for line in self:
            if line.is_delivery_expense_or_insurance():
                line.taxes_id = False
                continue
            fpos = line.order_id.fiscal_position_id
            if not fpos:
                continue
            line.taxes_id = (
                line.taxes_id | fpos.apply_tax_ids
            )

    def _prepare_account_move_line(self, move):
        res = super(PurchaseOrderLine, self)._prepare_account_move_line(move)
        res.update(
            {
                "l10n_br_is_delivery": self.l10n_br_is_delivery,
                "l10n_br_is_expense": self.l10n_br_is_expense,
                "l10n_br_is_insurance": self.l10n_br_is_insurance,
                "l10n_br_expense_amount": self.l10n_br_expense_amount,
                "l10n_br_insurance_amount": self.l10n_br_insurance_amount,
                "quantity": self.product_qty,
            }
        )
        return res
