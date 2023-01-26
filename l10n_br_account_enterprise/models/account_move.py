# © 2021 Danimar Ribeiro, Trustcode
# Part of Trustcode. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    def __getattribute__(self, name):
        if name == "tax_ids" and self:
            taxes = models.Model.__getattribute__(self, name)
            ctx = {}
            for item in self:
                ctx = item._prepare_tax_context()
            taxes = taxes.with_context(**ctx)
            return taxes
        else:
            return models.Model.__getattribute__(self, name)

    l10n_br_tax_rule_ids = fields.Many2many(
        comodel_name="account.fiscal.position.tax.rule",
        relation="account_move_line_tax_rule_rel",
        string="Regra Imposto",
    )

    def _get_computed_taxes(self):
        tax_ids = super(AccountMoveLine, self)._get_computed_taxes()
        if not self.move_id.fiscal_position_id:
            return tax_ids

        fpos = self.move_id.fiscal_position_id
        tax_rules = fpos.get_tax_rules(
            self.company_id, self.product_id, self.move_id.partner_id
        )
        self.l10n_br_tax_rule_ids = tax_rules

        return (
            tax_ids
            | tax_rules.mapped("tax_id")
            | tax_rules.mapped("tax_icms_st_id")
            | tax_rules.mapped("tax_fcp_st_id")
            | tax_rules.mapped("tax_icms_inter_id")
            | tax_rules.mapped("tax_icms_intra_id")
            | tax_rules.mapped("tax_icms_fcp_id")
        )

    def _prepare_tax_context(self):
        if not self:
            return {}

        tax_context = {}
        icms_rule = self.l10n_br_tax_rule_ids.filtered(
            lambda x: x.domain == "icms"
        )

        if icms_rule:
            tax_context.update(
                {
                    "l10n_br_cfop_id": icms_rule.l10n_br_cfop_id.code,
                    "icms_cst_normal": icms_rule.cst_icms or icms_rule.csosn_icms,
                    "incluir_ipi_base": icms_rule.incluir_ipi_base,
                    "icms_aliquota_reducao_base": icms_rule.reducao_icms,
                    "icms_aliquota_diferimento": icms_rule.aliquota_diferimento,
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
                    "cst_ipi": ipi_rule.cst_ipi,
                    "ipi_reducao_bc": ipi_rule.reducao_ipi,
                }
            )

        cofins_pis_rules = self.l10n_br_tax_rule_ids.filtered(
            lambda x: x.domain in ("cofins", "pis")
        )

        for rule in cofins_pis_rules:
            tax_context.update({
                "cst_{}".format(rule.domain): rule["cst_{}".format(rule.domain)]
            })

        tax_context.update(
            {
                "valor_frete": self[0].l10n_br_delivery_amount,
                "valor_seguro": self[0].l10n_br_insurance_amount,
                "outras_despesas": self[0].l10n_br_expense_amount,
            }
        )
        return tax_context

    @api.model
    def _get_price_total_and_subtotal_model(
        self,
        price_unit,
        quantity,
        discount,
        currency,
        product,
        partner,
        taxes,
        move_type,
    ):
        if taxes:
            ctx = self._prepare_tax_context()
            taxes = taxes.with_context(**ctx)
        return super(
            AccountMoveLine, self
        )._get_price_total_and_subtotal_model(
            price_unit,
            quantity,
            discount,
            currency,
            product,
            partner,
            taxes,
            move_type,
        )

    def _get_fields_onchange_balance_model(
        self,
        quantity,
        discount,
        amount_currency,
        move_type,
        currency,
        taxes,
        price_subtotal,
        force_computation=False
    ):
        # Fazendo isso para ele não recomputar caso tenha impostos brasileiros
        # pois ele vai fazer os calculos com o valor sem o preço incluso
        if len(taxes.filtered(lambda x: x.domain)) > 0:
            return {}
        return super(
            AccountMoveLine, self
        )._get_fields_onchange_balance_model(
            quantity,
            discount,
            amount_currency,
            move_type,
            currency,
            taxes,
            price_subtotal,
            force_computation,
        )

    def get_eletronic_line_vals(self):
        vals = super(AccountMoveLine, self).get_eletronic_line_vals()
        tax_ctx = {}
        taxes = {}

        currency = self.move_id and self.move_id.currency_id or None
        price = self.price_unit * (1 - (self.discount or 0.0) / 100.0)

        if self.tax_ids:
            tax_ctx = self._prepare_tax_context()
            taxes = self.tax_ids.with_context(**tax_ctx).compute_all(
                price,
                currency,
                self.quantity,
                product=self.product_id,
                partner=self.move_id.partner_id,
            )

        tax_vals = taxes.get("taxes", [])
        icms = next(
            (vals for vals in tax_vals if vals.get("domain") == "icms"), {}
        )
        icmsst = next(
            (vals for vals in tax_vals if vals.get("domain") == "icmsst"), {}
        )
        fcpst = next(
            (vals for vals in tax_vals if vals.get("domain") == "fcpst"), {}
        )
        icmsintra = next(
            (vals for vals in tax_vals if vals.get("domain") == "icms_intra"), {}
        )
        icmsinter = next(
            (vals for vals in tax_vals if vals.get("domain") == "icms_inter"), {}
        )
        icmsfcp = next(
            (vals for vals in tax_vals if vals.get("domain") == "fcp"), {}
        )
        ipi = next(
            (vals for vals in tax_vals if vals.get("domain") == "ipi"), {}
        )
        ii = next(
            (vals for vals in tax_vals if vals.get("domain") == "ii"), {}
        )
        pis = next(
            (vals for vals in tax_vals if vals.get("domain") == "pis"), {}
        )

        cofins = next(
            (vals for vals in tax_vals if vals.get("domain") == "cofins"), {}
        )

        iss = next(
            (vals for vals in tax_vals if vals.get("domain") == "iss"), {}
        )
        csll = next(
            (vals for vals in tax_vals if vals.get("domain") == "csll"), {}
        )
        irpj = next(
            (vals for vals in tax_vals if vals.get("domain") == "irpj"), {}
        )
        inss = next(
            (vals for vals in tax_vals if vals.get("domain") == "inss"), {}
        )
        irrf = next(
            (vals for vals in tax_vals if vals.get("domain") == "irrf"), {}
        )

        icms_rule = self.l10n_br_tax_rule_ids.filtered(
            lambda x: x.domain == "icms"
        )

        vals.update(
            {
                "valor_liquido": vals.get("valor_liquido", 0) + tax_ctx.get("valor_frete", 0),
                "cfop": tax_ctx.get("l10n_br_cfop_id", ""),
                'codigo_beneficio': icms_rule.l10n_br_fiscal_benefit or self.product_id.l10n_br_fiscal_benefit,
                "icms_cst": tax_ctx.get("icms_cst_normal"),
                #  'tributos_estimados': self.tributos_estimados,
                "ncm": self.product_id.l10n_br_ncm_id.code,
                # - ICMS -
                "icms_aliquota": icms.get("aliquota", 0.0),
                "icms_tipo_base": "3",
                "icms_aliquota_reducao_base": tax_ctx.get(
                    "icms_aliquota_reducao_base"
                ),
                "icms_base_calculo": icms.get("base", 0.0),
                "icms_valor": icms.get("amount", 0.0),
                "icms_aliquota_diferimento": tax_ctx.get("icms_aliquota_diferimento"),
                "icms_valor_original_operacao": round(icms.get("base", 0.0) * (icms.get("aliquota", 0.0) / 100.0), 2),
                "icms_valor_diferido": round(icms.get("base", 0.0) * (icms.get("aliquota", 0.0) / 100.0), 2) - icms.get("amount", 0.0),
                # - ICMS ST -
                "icms_st_aliquota": icmsst.get("aliquota", 0.0),
                "icms_st_aliquota_mva": tax_ctx.get(
                    "icms_st_aliquota_mva", 0.0
                ),
                "icms_st_aliquota_reducao_base": tax_ctx.get(
                    "icms_st_aliquota_reducao_base", 0.0
                ),
                "icms_st_base_calculo": icmsst.get("base", 0.0),
                "icms_st_valor": icmsst.get("amount", 0.0),
                # - FCP ST -
                "fcp_st_aliquota": fcpst.get("aliquota", 0.0),
                "fcp_st_valor": fcpst.get("amount", 0.0),
                # - ICMS Difal -
                "tem_difal": icms_rule.tem_difal,
                "icms_bc_uf_dest": icmsintra.get("base", 0.0),
                "icms_aliquota_uf_dest": icmsintra.get("aliquota", 0.0),
                "icms_aliquota_interestadual": icmsinter.get("aliquota", 0.0),

                "icms_uf_dest": icmsintra.get("amount", 0.0),
                "icms_uf_remet": icmsinter.get("amount", 0.0),

                # - ICMS FCP -
                "icms_aliquota_fcp_uf_dest": icmsfcp.get("aliquota", 0.0),
                "icms_fcp_uf_dest": icmsfcp.get("amount", 0.0),
                # - IPI -
                "ipi_cst": tax_ctx.get("cst_ipi", "99"),
                "ipi_aliquota": ipi.get("aliquota", 0.0),
                "ipi_base_calculo": ipi.get("base", 0.0) if ipi.get("aliquota") else 0,
                "ipi_valor": ipi.get("amount", 0.0),
                "ipi_reducao_bc": tax_ctx.get("ipi_reducao_bc", 0.0),
                # - II -
                "ii_base_calculo": ii.get("base", 0.0),
                "ii_valor": ii.get("amount", 0.0),
                # 'ii_valor_despesas': self.ii_valor_despesas,
                # 'ii_valor_iof': self.ii_valor_iof,
                # - PIS -
                "pis_cst": tax_ctx.get("cst_pis", "99"),
                "pis_aliquota": pis.get("aliquota", 0.0),
                "pis_base_calculo": pis.get("base", 0.0) if pis.get("aliquota") else 0,
                "pis_valor": pis.get("amount", 0.0)
                if pis.get("amount", 0.0) > 0
                else 0,
                "pis_valor_retencao": abs(pis.get("amount", 0.0))
                if pis.get("amount", 0.0) < 0
                else 0,
                # - COFINS -
                "cofins_cst": tax_ctx.get("cst_cofins", "99"),
                "cofins_aliquota": cofins.get("aliquota", 0.0),
                "cofins_base_calculo": cofins.get("base", 0.0) if cofins.get("aliquota") else 0,
                "cofins_valor": cofins.get("amount", 0.0)
                if cofins.get("amount", 0.0) > 0
                else 0,
                "cofins_valor_retencao": abs(cofins.get("amount", 0.0))
                if cofins.get("amount", 0.0) < 0
                else 0,
                # - ISS -
                "iss_aliquota": iss.get("aliquota", 0.0),
                "iss_base_calculo": iss.get("base", 0.0) if inss.get("aliquota") else 0,
                "iss_valor": iss.get("amount", 0.0),
                "iss_valor_retencao": abs(iss.get("amount", 0.0))
                if iss.get("amount", 0.0) < 0
                else 0,
                # - CSLL -
                "csll_aliquota": csll.get("aliquota", 0),
                "csll_base_calculo": csll.get("base", 0) if csll.get("aliquota") else 0,
                "csll_valor": abs(csll.get("amount", 0.0)),
                "csll_valor_retencao": abs(csll.get("amount", 0.0))
                if csll.get("amount", 0.0) < 0
                else 0,
                # - IRPJ -
                "irpj_aliquota": irpj.get("aliquota", 0),
                "irpj_base_calculo": irpj.get("base", 0) if irpj.get("aliquota") else 0,
                "irpj_valor": abs(irpj.get("amount", 0.0)),
                "irpj_valor_retencao": abs(irpj.get("amount"))
                if irpj.get("amount", 0.0) < 0
                else 0,
                # - Retencoes - INSS -
                "inss_aliquota": inss.get("aliquota", 0),
                "inss_base_calculo": inss.get("base", 0) if inss.get("aliquota") else 0,
                "inss_valor_retencao": abs(inss.get("amount", 0.0))
                if inss.get("amount", 0.0) < 0
                else 0,
                # - Retencoes - IRRF -
                "irrf_aliquota": irrf.get("aliquota", 0),
                "irrf_base_calculo": irrf.get("base", 0) if irrf.get("aliquota") else 0,
                "irrf_valor_retencao": abs(irrf.get("amount"))
                if irrf.get("amount", 0.0) < 0
                else 0,
            }
        )
        return vals
