# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro <danimaribeiro@gmail.com>, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import re
import logging

from datetime import datetime
from random import SystemRandom
from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class InvoiceEletronic(models.Model):
    _inherit = "invoice.eletronic"

    pos_order_id = fields.Many2one(
        "pos.order", string="Pedido POS", readonly=True
    )
    pos_reference = fields.Char(string="POS Reference")
    customer_cpf = fields.Char(string="CPF")

    def _get_variables_msg(self):
        variables = super(InvoiceEletronic, self)._get_variables_msg()
        variables.update({"order": self.pos_order_id, "eletronic": self})
        return variables

    @api.multi
    def _prepare_eletronic_invoice_values(self):
        vals = super(
            InvoiceEletronic, self
        )._prepare_eletronic_invoice_values()
        if self.model != "65":
            return vals
        vals["pag"][0]["tPag"] = self.metodo_pagamento
        vals["pag"][0]["vPag"] = "%.02f" % self.valor_pago
        vals["pag"][0]["vTroco"] = "%.02f" % self.troco or "0.00"
        if self.customer_cpf:
            vals.update(
                {
                    "dest": {
                        "tipo": "person",
                        "cnpj_cpf": re.sub("[^0-9]", "", self.customer_cpf),
                        "xNome": u"NF-E EMITIDA EM AMBIENTE DE HOMOLOGACAO -\
 SEM VALOR FISCAL"
                        if self.ambiente == "homologacao"
                        else None,
                        "enderDest": None,
                        "indIEDest": "9",
                    }
                }
            )
        return vals

    def _compute_legal_information(self):
        super(InvoiceEletronic, self)._compute_legal_information
        fiscal_ids = self.pos_order_id.fiscal_position_id.fiscal_observation_ids.filtered(
            lambda x: x.tipo == "fiscal"
        )
        obs_ids = self.pos_order_id.fiscal_position_id.fiscal_observation_ids.filtered(
            lambda x: x.tipo == "observacao"
        )

        prod_obs_ids = self.env["br_account.fiscal.observation"].browse()
        for item in self.pos_order_id.lines:
            prod_obs_ids |= item.product_id.fiscal_observation_ids

        fiscal_ids |= prod_obs_ids.filtered(lambda x: x.tipo == "fiscal")
        obs_ids |= prod_obs_ids.filtered(lambda x: x.tipo == "observacao")

        fiscal = self._compute_msg(fiscal_ids) + (
            self.invoice_id.fiscal_comment or ""
        )
        observacao = self._compute_msg(obs_ids) + (
            self.invoice_id.comment or ""
        )
        if self.informacoes_legais:
            self.informacoes_legais += fiscal
        else:
            self.informacoes_legais = fiscal
        if self.informacoes_complementares:
            self.informacoes_complementares += observacao
        else:
            self.informacoes_complementares = observacao

    def create_from_ui(self, orders):
        # Keep only new orders
        submitted_references = [o["name"] for o in orders]
        existing_edocs = self.search(
            [("pos_reference", "in", submitted_references)]
        )
        error_edocs = self.env["invoice.eletronic"]
        done_edocs = self.env["invoice.eletronic"]

        for edoc in existing_edocs:
            if edoc.state in ["error", "cancel"]:
                error_edocs += edoc
            else:
                done_edocs += edoc

        existing_references = set([o.pos_reference for o in done_edocs])

        edocs_to_save = [
            o for o in orders if o["name"] not in existing_references
        ]

        edoc_ids = done_edocs.ids or []
        error_edocs.unlink()

        for edoc_data in edocs_to_save:
            if edoc_data.get("to_invoice"):
                continue
            edoc_id = self.create(self._prepare_edoc_fields(edoc_data))
            edoc_id.validate_invoice()
            edoc_id.action_post_validate()
            edoc_ids.append(edoc_id.id)

        return edoc_ids

    def get_approximate_taxes(self, product, price):
        ncm = product.fiscal_classification_id

        tributos_estimados_federais = price * (ncm.federal_nacional / 100)
        tributos_estimados_estaduais = price * (ncm.estadual_imposto / 100)
        tributos_estimados_municipais = price * (ncm.municipal_imposto / 100)

        return "%.02f" % (
            tributos_estimados_federais
            + tributos_estimados_estaduais
            + tributos_estimados_municipais
        )

    def get_total_tributes(self, eletronic_item_values):
        trib = []
        for item in eletronic_item_values:
            val = item[2].get("tributos_estimados")
            if val:
                trib.append(float(val))
        return sum(trib)

    def _prepare_tax_context(self, vals):
        return {
            "icms_st_aliquota_mva": vals.get("icms_st_aliquota_mva"),
            "icms_aliquota_reducao_base": vals.get(
                "icms_aliquota_reducao_base"
            ),
            "icms_st_aliquota_reducao_base": vals.get(
                "icms_st_aliquota_reducao_base"
            ),
            "icms_base_calculo": vals.get("icms_base_calculo"),
            "pis_base_calculo": vals.get("pis_base_calculo"),
            "cofins_base_calculo": vals.get("cofins_base_calculo"),
        }

    def _prepare_edoc_item_fields(
        self, line, fiscal_pos, partner, company, pricelist
    ):
        if not line:
            return
        line_vals = line[2]
        product = self.env["product.product"].browse(
            line_vals.get("product_id")
        )
        tax_values = fiscal_pos.map_tax_extra_values(
            company, product, partner
        )

        empty = self.env["account.tax"]
        tax_ids = (
            tax_values.get("tax_icms_id", empty)
            + tax_values.get("tax_icms_st_id", empty)
            + tax_values.get("tax_ipi_id", empty)
            + tax_values.get("tax_pis_id", empty)
            + tax_values.get("tax_cofins_id", empty)
            + tax_values.get("tax_ii_id", empty)
            + tax_values.get("tax_issqn_id", empty)
        )

        vals = {
            "name": line_vals.get("name"),
            "product_id": product.id,
            "tipo_produto": product.fiscal_type,
            "cfop": tax_values["cfop_id"].code
            if tax_values.get("cfop_id", False)
            else False,
            "cest": product.cest
            or product.fiscal_classification_id.cest
            or "",
            "uom_id": product.uom_id.id,
            "ncm": product.fiscal_classification_id.code,
            "quantidade": line_vals.get("qty"),
            "preco_unitario": line_vals.get("price_unit"),
            "valor_bruto": line_vals.get("price_subtotal_incl"),
            "valor_liquido": line_vals.get("price_subtotal"),
            "origem": product.origin,
            "tributos_estimados": self.get_approximate_taxes(
                product, line_vals.get("price_subtotal")
            ),
            # - ICMS -
            "icms_cst": tax_values.get("icms_cst_normal", False)
            or tax_values.get("icms_csosn_simples", False),
            "icms_tipo_base": "3",
            "icms_aliquota_reducao_base": tax_values.get(
                "icms_aliquota_reducao_base", False
            ),
            # - ICMS ST -
            "icms_st_aliquota": 0,
            "icms_st_aliquota_mva": 0,
            "icms_st_aliquota_reducao_base": tax_values.get(
                "icms_st_aliquota_reducao_base", False
            ),
            "icms_st_base_calculo": 0,
            "icms_st_valor": 0,
            # - Simples Nacional -
            "icms_aliquota_credito": 0,
            "icms_valor_credito": 0,
            # - II -
            "ii_base_calculo": 0,
            "ii_valor_despesas": 0,
            "ii_valor": 0,
            "ii_valor_iof": 0,
            # - IPI -
            "ipi_cst": tax_values.get("ipi_cst", False),
            # - PIS -
            "pis_cst": tax_values.get("pis_cst", False),
            # - COFINS -
            "cofins_cst": tax_values.get("cofins_cst", False),
            # - ISSQN -
            "issqn_codigo": 0,
            "issqn_aliquota": 0,
            "issqn_base_calculo": 0,
            "issqn_valor": 0,
            "issqn_valor_retencao": 0.00,
        }

        taxes_ids = tax_ids.filtered(
            lambda tax: tax.company_id.id == company.id
        )
        if fiscal_pos:
            taxes_ids = fiscal_pos.map_tax(taxes_ids, product, partner)
            price = line_vals.get("price_unit") * (
                1 - (line_vals.get("discount") or 0.0) / 100.0
            )
            taxes = {"taxes": []}
            if taxes_ids:
                ctx = self._prepare_tax_context(vals)
                taxes_ids = taxes_ids.with_context(**ctx)
                taxes = taxes_ids.compute_all(
                    price,
                    pricelist.currency_id,
                    line_vals.get("qty"),
                    product=product,
                    partner=partner or False,
                )
            for tax in taxes["taxes"]:
                tax_id = self.env["account.tax"].browse(tax["id"])
                if tax_id.domain == "icms":
                    vals.update(
                        {
                            "icms_aliquota": tax_id.amount,
                            "icms_base_calculo": tax.get("base", 0.00),
                            "icms_valor": tax.get("amount", 0.00),
                        }
                    )
                if tax_id.domain == "ipi":
                    vals.update(
                        {
                            "ipi_aliquota": tax_id.amount,
                            "ipi_base_calculo": tax.get("base", 0.00),
                            "ipi_valor": tax.get("amount", 0.00),
                        }
                    )
                if tax_id.domain == "pis":
                    vals.update(
                        {
                            "pis_aliquota": tax_id.amount,
                            "pis_base_calculo": tax.get("base", 0.00),
                            "pis_valor": tax.get("amount", 0.00),
                        }
                    )
                if tax_id.domain == "cofins":
                    vals.update(
                        {
                            "cofins_aliquota": tax_id.amount,
                            "cofins_base_calculo": tax.get("base", 0.00),
                            "cofins_valor": tax.get("amount", 0.00),
                        }
                    )
        line[2] = vals
        return line

    def _prepare_edoc_fields(self, ui_order):
        fiscal_position = self.env["account.fiscal.position"].browse(
            ui_order["fiscal_position_id"]
        )
        partner = self.env["res.partner"].browse(ui_order["partner_id"])
        company = self.env.user.company_id
        pricelist = self.env["product.pricelist"].browse(
            ui_order["pricelist_id"]
        )
        pos_session = self.env["pos.session"].browse(
            ui_order["pos_session_id"]
        )

        journal = self.env["account.journal"].browse(
            ui_order.get("statement_ids")[0][2].get("journal_id")
        )

        if pos_session.sequence_number <= ui_order["sequence_number"]:
            pos_session.write(
                {"sequence_number": ui_order["sequence_number"] + 1}
            )
            pos_session.refresh()

        numero = (
            fiscal_position.product_serie_id.internal_sequence_id.next_by_id()
        )

        vals = {
            "pos_reference": ui_order["name"],
            "code": ui_order.get("sequence_number"),
            "name": u"Documento Eletrônico: nº %d"
            % ui_order.get("sequence_number"),
            "company_id": company.id,
            "schedule_user_id": ui_order.get("user_id"),
            "date_order": ui_order["creation_date"],
            "pricelist_id": ui_order["pricelist_id"],
            "state": "draft",
            "tipo_operacao": "saida",
            "model": "65",
            "ind_dest": "1",
            "ind_ie_dest": "9",
            "ambiente": "homologacao"
            if company.tipo_ambiente == "2"
            else "producao",
            "serie": fiscal_position.product_serie_id.id,
            "numero": numero,
            "numero_nfe": numero,
            "numero_controle": "".join(
                [str(SystemRandom().randrange(9)) for i in range(8)]
            ),
            "data_emissao": datetime.now(),
            "data_fatura": datetime.now(),
            "finalidade_emissao": "1",
            "partner_id": ui_order.get("partner_id"),
            "customer_cpf": ui_order.get("customer_cpf", ""),
            "payment_term_id": None,
            "fiscal_position_id": fiscal_position.id,
            "ind_final": fiscal_position.ind_final,
            "ind_pres": fiscal_position.ind_pres,
            "metodo_pagamento": journal.metodo_pagamento,
            "troco": abs(
                sum(
                    payment[2].get("amount")
                    for payment in ui_order.get("statement_ids")
                    if payment[2].get("amount") < 0
                )
            ),
            "valor_pago": sum(
                payment[2].get("amount")
                for payment in ui_order.get("statement_ids")
                if payment[2].get("amount") > 0
            ),
            "eletronic_item_ids": [
                self._prepare_edoc_item_fields(
                    line, fiscal_position, partner, company, pricelist
                )
                for line in ui_order["lines"]
            ]
            if ui_order["lines"]
            else False,
        }

        base_icms = 0
        for pos_line in vals.get("eletronic_item_ids"):
            base_icms += pos_line[2].get("icms_base_calculo") or 0

        vals.update(
            {
                "valor_estimado_tributos": self.get_total_tributes(
                    vals.get("eletronic_item_ids")
                ),
                "valor_icms": sum(
                    line[2].get("icms_valor", 0)
                    for line in vals.get("eletronic_item_ids")
                ),
                "valor_pis": sum(
                    line[2].get("pis_valor", 0)
                    for line in vals.get("eletronic_item_ids")
                ),
                "valor_cofins": sum(
                    line[2].get("cofins_valor", 0)
                    for line in vals.get("eletronic_item_ids")
                ),
                "valor_ii": 0,
                "valor_bruto": ui_order["amount_total"]
                - ui_order["amount_tax"],
                "valor_desconto": ui_order["amount_tax"],
                "valor_final": ui_order["amount_total"],
                "valor_bc_icms": base_icms,
                "valor_bc_icmsst": 0,
            }
        )
        return vals
