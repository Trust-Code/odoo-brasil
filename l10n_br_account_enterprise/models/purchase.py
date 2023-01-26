# © 2021 Danimar Ribeiro, Trustcode
# Part of Trustcode. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    l10n_br_tax_rule_ids = fields.Many2many(
        comodel_name="account.fiscal.position.tax.rule",
        relation="purchase_order_line_tax_rule_rel",
        string="Regra Imposto",
    )

    def __getattribute__(self, name):
        if name == "taxes_id":
            taxes = models.Model.__getattribute__(self, name)
            ctx = self._prepare_tax_context()
            taxes = taxes.with_context(**ctx)
            return taxes
        else:
            return models.Model.__getattribute__(self, name)

    def _prepare_tax_context(self):
        tax_context = {}

        icms_rule = self.l10n_br_tax_rule_ids.filtered(
            lambda x: x.domain == "icms"
        )

        if icms_rule:
            tax_context.update(
                {
                    "l10n_br_cfop_id": icms_rule.l10n_br_cfop_id.code,
                    "icms_cst_normal": icms_rule.cst_icms,
                    "incluir_ipi_base": icms_rule.incluir_ipi_base,
                    "icms_aliquota_reducao_base": icms_rule.reducao_icms,
                    "icms_st_aliquota_mva": icms_rule.aliquota_mva,
                    "icms_st_aliquota_reducao_base": icms_rule.reducao_icms_st,
                    "icms_st_aliquota_deducao": icms_rule.icms_st_aliquota_deducao,
                }
            )

        issqn_rule = self.l10n_br_tax_rule_ids.filtered(
            lambda x: x.domain == "issqn"
        )

        if issqn_rule:
            tax_context.update(
                {
                    "l10n_br_cfop_id": issqn_rule.l10n_br_cfop_id.code,
                    "l10n_br_issqn_deduction": issqn_rule.l10n_br_issqn_deduction,
                }
            )

        ipi_rule = self.l10n_br_tax_rule_ids.filtered(
            lambda x: x.domain == "ipi"
        )

        if ipi_rule:
            tax_context.update(
                {
                    "ipi_reducao_bc": ipi_rule.reducao_ipi,
                }
            )

        tax_context.update(
            {
                "valor_frete": self.l10n_br_delivery_amount,
                "valor_seguro": self.l10n_br_insurance_amount,
                "outras_despesas": self.l10n_br_expense_amount,
            }
        )
        return tax_context

    def _compute_tax_id(self):
        super(PurchaseOrderLine, self)._compute_tax_id()
        for line in self.filtered(
            lambda x: not x.is_delivery_expense_or_insurance()
        ):
            fpos = line.order_id.fiscal_position_id
            if not fpos:
                continue
            tax_rules = fpos.get_tax_rules(
                line.order_id.company_id,
                line.product_id,
                line.order_id.partner_id,
            )
            line.l10n_br_tax_rule_ids = tax_rules
            line.taxes_id = (
                line.taxes_id
                | tax_rules.mapped("tax_id")
                | tax_rules.mapped("tax_icms_st_id")
                | tax_rules.mapped("tax_fcp_st_id")
                | tax_rules.mapped("tax_icms_inter_id")
                | tax_rules.mapped("tax_icms_intra_id")
                | tax_rules.mapped("tax_icms_fcp_id")
            )
