# -*- coding: utf-8 -*-
# © 2016 Alessandro Fernandes Martini <alessandrofmartini@gmail.com>, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from datetime import datetime
from random import SystemRandom
from odoo import api, models, fields
from odoo.exceptions import UserError


class PosOrder(models.Model):
    _inherit = "pos.order"

    def _compute_nfe_number(self):
        for item in self:
            docs = self.env["eletronic.document"].search(
                [("pos_order_id", "=", item.id)]
            )
            if docs:
                item.nfe_number = docs[0].numero
                item.nfe_exception_number = docs[0].numero
                item.nfe_exception = docs[0].state in ("error", "denied")
                item.sending_nfe = docs[0].state == "draft"
                item.nfe_status = "%s - %s" % (
                    docs[0].codigo_retorno,
                    docs[0].mensagem_retorno,
                )

    ambiente_nfe = fields.Selection(
        string="Ambiente NFe",
        related="company_id.l10n_br_tipo_ambiente",
        readonly=True,
    )
    sending_nfe = fields.Boolean(
        string="Enviando NFe?", compute="_compute_nfe_number"
    )
    nfe_exception = fields.Boolean(
        string="Problemas na NFe?", compute="_compute_nfe_number"
    )
    nfe_status = fields.Char(
        string="Mensagem NFe", compute="_compute_nfe_number"
    )
    nfe_number = fields.Integer(
        string=u"Número NFe", compute="_compute_nfe_number"
    )
    nfe_exception_number = fields.Integer(
        string=u"Número NFe", compute="_compute_nfe_number"
    )
    numero = fields.Integer()
    numero_controle = fields.Integer()
    customer_cpf = fields.Char(string="CPF cliente")

    @api.model
    def _order_fields(self, ui_order):
        res = super(PosOrder, self)._order_fields(ui_order)
        res.update({"customer_cpf": ui_order["customer_cpf"] or False})
        return res

    def action_preview_danfe(self):
        docs = self.env["eletronic.document"].search(
            [("pos_order_id", "=", self.id)]
        )

        if not docs:
            raise UserError("Não existe um E-Doc relacionado à este pedido")

        for doc in docs:
            if doc.state == "draft":
                raise UserError(
                    "Nota Fiscal de consumidor na fila de envio. Aguarde!"
                )

        action = self.env.ref("br_nfe.report_br_nfe_danfe").report_action(
            docs
        )
        return action

    @api.model
    def _process_order(self, pos_order, draft, existing_order):
        num_controle = int(
            "".join([str(SystemRandom().randrange(9)) for i in range(8)])
        )

        res = super(PosOrder, self)._process_order(
            pos_order, draft, existing_order
        )

        res = self.env["pos.order"].browse(res)

        res.numero_controle = str(num_controle)
        if not res.fiscal_position_id:
            res.fiscal_position_id = (
                res.session_id.config_id.default_fiscal_position_id.id
            )

        res.numero = res.company_id.l10n_br_nfe_sequence.next_by_id()

        for line in res.lines:

            tax_ids = line.order_id.fiscal_position_id.apply_tax_ids

            other_taxes = line.tax_ids.filtered(lambda x: not x.domain)
            tax_ids |= other_taxes
            line.update(
                {"tax_ids": [(6, None, [x.id for x in tax_ids if x])]}
            )

        foo = self._prepare_edoc_vals(res)
        eletronic = self.env["eletronic.document"].create(foo)
        eletronic.validate_invoice()
        eletronic.action_post_validate()
        return res.id

    def _prepare_edoc_item_vals(self, pos_line):

        pis = pos_line.tax_ids.filtered(lambda x: x.domain == "pis")
        cofins = pos_line.tax_ids.filtered(lambda x: x.domain == "cofins")
        ipi = pos_line.tax_ids.filtered(lambda x: x.domain == "ipi")

        fiscal_pos = pos_line.order_id.fiscal_position_id

        vals = {
            "name": pos_line.name,
            "product_id": pos_line.product_id.id,
            "cfop": fiscal_pos.l10n_br_cfop_id.code,
            "cest": pos_line.product_id.l10n_br_cest
            or pos_line.product_id.l10n_br_ncm_id.cest
            or "",
            "uom_id": pos_line.product_id.uom_id.id,
            "ncm": pos_line.product_id.l10n_br_ncm_id.code,
            "quantidade": pos_line.qty,
            "preco_unitario": pos_line.price_unit,
            "valor_bruto": pos_line.price_subtotal_incl,
            "valor_liquido": pos_line.price_subtotal,
            "tributos_estimados": pos_line.get_approximate_taxes(),
            # - ICMS -
            "icms_cst": fiscal_pos.csosn_icms,
            # 'icms_aliquota': pos_line.aliquota_icms,
            # 'icms_tipo_base': '3',
            # 'icms_aliquota_reducao_base':
            #     pos_line.icms_aliquota_reducao_base,
            # 'icms_base_calculo': pos_line.base_icms,
            # 'icms_valor': pos_line.valor_icms,
            # # - ICMS ST -
            # 'icms_st_aliquota': 0,
            # 'icms_st_aliquota_mva': 0,
            # 'icms_st_aliquota_reducao_base': pos_line.\
            # icms_st_aliquota_reducao_base,
            # 'icms_st_base_calculo': 0,
            # 'icms_st_valor': 0,
            # - Simples Nacional -
            "icms_aliquota_credito": fiscal_pos.icms_aliquota_credito,
            "icms_valor_credito": round(
                pos_line.price_subtotal
                * fiscal_pos.icms_aliquota_credito
                / 100,
                2,
            ),
            # - II -
            # "ii_base_calculo": 0,
            # "ii_valor_despesas": 0,
            # "ii_valor": 0,
            # "ii_valor_iof": 0,
            # - IPI -
            "ipi_cst": "99",
            "ipi_aliquota": ipi.amount or 0,
            "ipi_base_calculo": pos_line.price_subtotal or 0,
            "ipi_valor": round(
                (ipi.amount or 0) * pos_line.price_subtotal / 100, 2
            ),
            # - PIS -
            "pis_cst": "49",
            "pis_aliquota": pis.amount or 0,
            "pis_base_calculo": pos_line.price_subtotal or 0,
            "pis_valor": round(
                (pis.amount or 0) * pos_line.price_subtotal / 100, 2
            ),
            # - COFINS -
            "cofins_cst": "49",
            "cofins_aliquota": cofins.amount or 0,
            "cofins_base_calculo": pos_line.price_subtotal or 0,
            "cofins_valor": round(
                (cofins.amount or 0) * pos_line.price_subtotal / 100, 2
            ),
            # - ISS -
            "iss_aliquota": 0,
            "iss_base_calculo": 0,
            "iss_valor": 0,
            "iss_valor_retencao": 0.00,
        }
        return vals

    def _prepare_edoc_vals(self, pos):
        vals = {
            "pos_order_id": pos.id,
            "name": u"Documento Eletrônico: nº %d" % pos.sequence_number,
            "company_id": pos.company_id.id,
            "state": "draft",
            "tipo_operacao": "saida",
            "cod_regime_tributario": "1",
            "model": "nfce",
            "ind_dest": "1",
            "ind_ie_dest": "9",
            "ambiente": pos.company_id.l10n_br_tipo_ambiente,
            "serie_documento": pos.fiscal_position_id.serie_nota_fiscal,
            "numero": pos.numero,
            "numero_nfe": pos.numero,
            "numero_controle": pos.numero_controle,
            "data_emissao": datetime.now(),
            "finalidade_emissao": "1",
            "partner_id": pos.partner_id.id,
            "customer_cpf": pos.customer_cpf,
            "payment_term_id": None,
            "fiscal_position_id": pos.fiscal_position_id.id,
            "ind_final": pos.fiscal_position_id.ind_final,
            "ind_pres": pos.fiscal_position_id.ind_pres,
            "metodo_pagamento": pos.payment_ids[
                0
            ].payment_method_id.metodo_pagamento,
            "troco": abs(
                sum(
                    payment.amount
                    for payment in pos.payment_ids
                    if payment.amount < 0
                )
            ),
            "valor_pago": sum(
                payment.amount
                for payment in pos.payment_ids
                if payment.amount > 0
            ),
        }

        # base_icms = 0
        # base_cofins = 0
        # base_pis = 0
        eletronic_items = []
        for pos_line in pos.lines:
            eletronic_items.append(
                (0, 0, self._prepare_edoc_item_vals(pos_line))
            )
            # base_icms += pos_line.base_icms
            # base_pis += pos_line.base_pis
            # base_cofins += pos_line.base_cofins

        vals["document_line_ids"] = eletronic_items
        # vals['valor_estimado_tributos'] = \
        #     self.get_total_tributes(eletronic_items)
        # vals['valor_icms'] = pos.total_icms
        # vals['valor_pis'] = pos.total_pis
        # vals['valor_cofins'] = pos.total_cofins
        # vals['valor_ii'] = 0
        # vals['valor_bruto'] = pos.amount_total - pos.amount_tax
        # vals['valor_desconto'] = pos.amount_tax
        # vals['valor_final'] = pos.amount_total
        # vals['valor_bc_icms'] = base_icms
        # vals['valor_bc_icmsst'] = 0
        return vals

    def get_total_tributes(self, values):
        trib = []
        for item in values:
            val = item[2].get("tributos_estimados")
            if val:
                trib.append(float(val))
        return sum(trib)

    def _compute_total_edocs(self):
        for item in self:
            item.total_edocs = self.env["eletronic.document"].search_count(
                [("pos_order_id", "=", item.id)]
            )

    total_edocs = fields.Integer(
        string="Total NFe", compute=_compute_total_edocs
    )

    def action_view_edocs(self):
        if self.total_edocs == 1:
            edoc = self.env["eletronic.document"].search(
                [("pos_order_id", "=", self.id)], limit=1
            )
            dummy, act_id = self.env["ir.model.data"].get_object_reference(
                "br_account_einvoice", "action_sped_base_eletronic_doc"
            )
            dummy, view_id = self.env["ir.model.data"].get_object_reference(
                "br_account_einvoice", "br_account_invoice_eletronic_form"
            )
            vals = self.env["ir.actions.act_window"].browse(act_id).read()[0]
            vals["view_id"] = (view_id, u"sped.eletronic.doc.form")
            vals["views"][1] = (view_id, u"form")
            vals["views"] = [vals["views"][1], vals["views"][0]]
            vals["res_id"] = edoc.id
            vals["search_view"] = False
            return vals
        else:
            dummy, act_id = self.env["ir.model.data"].get_object_reference(
                "br_account_einvoice", "action_sped_base_eletronic_doc"
            )
            vals = self.env["ir.actions.act_window"].browse(act_id).read()[0]
            return vals

    @api.model
    def _amount_line_tax(self, line, fiscal_position_id):
        taxes = line.tax_ids.filtered(
            lambda t: t.company_id.id == line.order_id.company_id.id
        )
        if fiscal_position_id:
            taxes = fiscal_position_id.map_tax(
                taxes, line.product_id, line.order_id.partner_id
            )
        price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
        taxes = taxes.compute_all(
            price,
            line.order_id.pricelist_id.currency_id,
            line.qty,
            product=line.product_id,
            partner=line.order_id.partner_id or False,
        )
        return taxes["total_included"] - taxes["total_excluded"]


class PosOrderLine(models.Model):
    _inherit = "pos.order.line"

    def get_approximate_taxes(self):
        ncm = self.product_id.l10n_br_ncm_id

        tributos_estimados_federais = self.price_subtotal * (
            ncm.federal_nacional / 100
        )
        tributos_estimados_estaduais = self.price_subtotal * (
            ncm.estadual_imposto / 100
        )
        tributos_estimados_municipais = self.price_subtotal * (
            ncm.municipal_imposto / 100
        )

        return "%.02f" % (
            tributos_estimados_federais
            + tributos_estimados_estaduais
            + tributos_estimados_municipais
        )
