# © 2021 Danimar Ribeiro, Trustcode
# Part of Trustcode. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from odoo.addons.l10n_br_account.models.cst import CST_ICMS
from odoo.addons.l10n_br_account.models.cst import CSOSN_SIMPLES
from odoo.addons.l10n_br_account.models.cst import CST_IPI
from odoo.addons.l10n_br_account.models.cst import CST_PIS_COFINS


class AccountFiscalPositionTaxRule(models.Model):
    _name = "account.fiscal.position.tax.rule"
    _description = "Regras de Impostos"
    _order = "sequence"

    sequence = fields.Integer(string="Sequência")
    name = fields.Char(string="Descrição", size=100)
    domain = fields.Selection(
        [
            ("icms", "ICMS"),
            ("pis", "PIS"),
            ("cofins", "COFINS"),
            ("ipi", "IPI"),
            ("issqn", "ISSQN"),
            ("ii", "II"),
            ("csll", "CSLL"),
            ("irpj", "IRPJ"),
            ("inss", "INSS"),
            ("outros", "Outros"),
        ],
        string="Tipo",
    )
    fiscal_position_id = fields.Many2one(
        "account.fiscal.position", string="Posição Fiscal"
    )

    state_ids = fields.Many2many(
        "res.country.state",
        string="Estado Destino",
        domain=[("country_id.code", "=", "BR")],
    )
    fiscal_category_ids = fields.Many2many(
        comodel_name="product.fiscal.category",
        string="Categorias Fiscais",
        relation="account_fiscal_position_tax_rule_prod_fiscal_category_rel",
    )
    tipo_produto = fields.Selection(
        [("product", "Produto"), ("service", "Serviço")],
        string="Tipo produto",
        default="product",
    )

    product_fiscal_classification_ids = fields.Many2many(
        comodel_name="account.ncm",
        string="Classificação Fiscal",
        relation="account_fiscal_position_tax_rule_prod_fiscal_clas_relation",
    )

    cst_icms = fields.Selection(CST_ICMS, string="CST ICMS")
    csosn_icms = fields.Selection(CSOSN_SIMPLES, string="CSOSN ICMS")
    cst_pis = fields.Selection(CST_PIS_COFINS, string="CST PIS")
    cst_cofins = fields.Selection(CST_PIS_COFINS, string="CST COFINS")
    cst_ipi = fields.Selection(CST_IPI, string="CST IPI")
    l10n_br_cfop_id = fields.Many2one("nfe.cfop", string="CFOP")
    l10n_br_fiscal_benefit = fields.Char(string="Benefício Fiscal", size=10)
    tax_id = fields.Many2one("account.tax", string="Imposto")
    tax_icms_st_id = fields.Many2one(
        "account.tax", string="ICMS ST", domain=[("domain", "=", "icmsst")]
    )
    tax_fcp_st_id = fields.Many2one(
        "account.tax", string="FCP ST", domain=[("domain", "=", "fcpst")]
    )
    icms_aliquota_credito = fields.Float(string="% Crédito de ICMS")
    incluir_ipi_base = fields.Boolean(string="Incl. IPI na base ICMS")
    reducao_icms = fields.Float(string="Redução de base")
    reducao_icms_st = fields.Float(string="Redução de base ST")
    reducao_ipi = fields.Float(string="Redução de base IPI")
    l10n_br_issqn_deduction = fields.Float(string="% Dedução de base ISS")
    aliquota_mva = fields.Float(string="Alíquota MVA")
    aliquota_diferimento = fields.Float(string="% de Diferimento")
    icms_st_aliquota_deducao = fields.Float(
        string="% ICMS Próprio",
        help="Alíquota interna ou interestadual aplicada \
         sobre o valor da operação para deduzir do ICMS ST - Para empresas \
         do Simples Nacional ou usado em casos onde existe apenas ST sem ICMS",
    )
    tem_difal = fields.Boolean(string="Aplicar Difal?")
    tax_icms_inter_id = fields.Many2one(
        "account.tax",
        help="Alíquota utilizada na operação Interestadual",
        string="ICMS Inter",
        domain=[("domain", "=", "icms_inter")],
    )
    tax_icms_intra_id = fields.Many2one(
        "account.tax",
        help="Alíquota interna do produto no estado destino",
        string="ICMS Intra",
        domain=[("domain", "=", "icms_intra")],
    )
    tax_icms_fcp_id = fields.Many2one(
        "account.tax", string="% FCP", domain=[("domain", "=", "fcp")]
    )


class AccountFiscalPosition(models.Model):
    _inherit = "account.fiscal.position"

    icms_tax_rule_ids = fields.One2many(
        "account.fiscal.position.tax.rule",
        "fiscal_position_id",
        string="Regras ICMS",
        domain=[("domain", "=", "icms")],
        copy=True,
    )
    ipi_tax_rule_ids = fields.One2many(
        "account.fiscal.position.tax.rule",
        "fiscal_position_id",
        string="Regras IPI",
        domain=[("domain", "=", "ipi")],
        copy=True,
    )
    pis_tax_rule_ids = fields.One2many(
        "account.fiscal.position.tax.rule",
        "fiscal_position_id",
        string="Regras PIS",
        domain=[("domain", "=", "pis")],
        copy=True,
    )
    cofins_tax_rule_ids = fields.One2many(
        "account.fiscal.position.tax.rule",
        "fiscal_position_id",
        string="Regras COFINS",
        domain=[("domain", "=", "cofins")],
        copy=True,
    )
    issqn_tax_rule_ids = fields.One2many(
        "account.fiscal.position.tax.rule",
        "fiscal_position_id",
        string="Regras ISSQN",
        domain=[("domain", "=", "issqn")],
        copy=True,
    )
    ii_tax_rule_ids = fields.One2many(
        "account.fiscal.position.tax.rule",
        "fiscal_position_id",
        string="Regras II",
        domain=[("domain", "=", "ii")],
        copy=True,
    )
    irpj_tax_rule_ids = fields.One2many(
        "account.fiscal.position.tax.rule",
        "fiscal_position_id",
        string="Regras IRPJ",
        domain=[("domain", "=", "irpj")],
        copy=True,
    )
    csll_tax_rule_ids = fields.One2many(
        "account.fiscal.position.tax.rule",
        "fiscal_position_id",
        string="Regras CSLL",
        domain=[("domain", "=", "csll")],
        copy=True,
    )
    inss_tax_rule_ids = fields.One2many(
        "account.fiscal.position.tax.rule",
        "fiscal_position_id",
        string="Regras INSS",
        domain=[("domain", "=", "inss")],
        copy=True,
    )

    def get_tax_rules(self, company_id, product_id, partner_id):
        TaxRuleModel = self.env["account.fiscal.position.tax.rule"]
        if not product_id:
            return TaxRuleModel
        tax_rule_ids = self.map_tax_extra_values(
            company_id,
            product_id,
            partner_id,
        )
        return TaxRuleModel.browse(tax_rule_ids)

    def _filter_rules(self, type_tax, partner, product, state):
        # Get the rule by sql
        sql = """WITH rule_points AS (
        SELECT id, domain, l10n_br_cfop_id, tax_id, cst_icms, reducao_icms,
            incluir_ipi_base, tax_icms_st_id, aliquota_mva, reducao_icms_st,
            icms_st_aliquota_deducao, tem_difal, tax_icms_inter_id,
            tax_icms_intra_id, tax_icms_fcp_id, csosn_icms,
            icms_aliquota_credito, cst_ipi, reducao_ipi, cst_pis, cst_cofins,
            l10n_br_issqn_deduction,
                CASE
                    WHEN fc.product_fiscal_category_id = %s --fiscal_category_id
                    THEN 1 ELSE 0
                END AS fiscal_category,
                CASE
                    WHEN ncm.account_ncm_id = %s --ncm_id
                    THEN 1 ELSE 0
                END AS ncm,
                CASE
                    WHEN state.res_country_state_id = %s --state_id
                    THEN 1 ELSE 0
                END AS state
        FROM account_fiscal_position_tax_rule tr
        LEFT JOIN account_fiscal_position_tax_rule_prod_fiscal_category_rel fc
                ON fc.account_fiscal_position_tax_rule_id = tr.id
        LEFT JOIN account_fiscal_position_tax_rule_prod_fiscal_clas_relation ncm
                ON ncm.account_fiscal_position_tax_rule_id = tr.id
        LEFT JOIN account_fiscal_position_tax_rule_res_country_state_rel state
                ON state.account_fiscal_position_tax_rule_id = tr.id
        WHERE tr.fiscal_position_id = %s --fiscal_position_id
                AND tr.tipo_produto = %s --'product'
                AND tr.domain = %s -- tax
        )
        SELECT id, l10n_br_cfop_id, tax_id, cst_icms, reducao_icms,
            incluir_ipi_base, tax_icms_st_id, aliquota_mva, reducao_icms_st,
            icms_st_aliquota_deducao, tem_difal, tax_icms_inter_id,
            tax_icms_intra_id, tax_icms_fcp_id, csosn_icms,
            icms_aliquota_credito, cst_ipi, reducao_ipi, cst_pis, cst_cofins,
            l10n_br_issqn_deduction,
            (fiscal_category + ncm + state) as rule_points
        FROM rule_points
        ORDER BY rule_points DESC"""
  
        self.env.cr.execute(
            sql,
            (
                product.l10n_br_fiscal_category_id.id or 0,
                product.l10n_br_ncm_id.id or 0,
                state.id,
                self.id,
                "product" if product.type == "consu" else product.type,
                type_tax,
            ),
        )
        rules = self.env.cr.fetchall()
        if rules:
            rule_ids = self.env["account.fiscal.position.tax.rule"].browse(
                list(dict.fromkeys(map(lambda x: x[0], rules)))
            )
            for rule in rule_ids:
                if (
                    (state in rule.state_ids or not rule.state_ids)
                    and (
                        product.l10n_br_fiscal_category_id
                        in rule.fiscal_category_ids
                        or not rule.fiscal_category_ids
                    )
                    and (
                        product.l10n_br_ncm_id
                        in rule.product_fiscal_classification_ids
                        or not rule.product_fiscal_classification_ids
                    )
                ):
                    return rule.id
        return False

    @api.model
    def map_tax_extra_values(self, company, product, partner):
        to_state = partner.state_id

        taxes = (
            "icms",
            "simples",
            "ipi",
            "pis",
            "cofins",
            "issqn",
            "ii",
            "irpj",
            "csll",
            "inss",
        )
        rules = []
        for tax in taxes:
            rules.append(self._filter_rules(tax, partner, product, to_state))
        return [item for item in rules if item]
