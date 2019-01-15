# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro <danimaribeiro@gmail.com>, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from datetime import datetime
from random import SystemRandom

from odoo import api, fields, models
from odoo.exceptions import UserError


TYPE2EDOC = {
    'out_invoice': 'saida',        # Customer Invoice
    'in_invoice': 'entrada',          # Vendor Bill
    'out_refund': 'entrada',        # Customer Refund
    'in_refund': 'saida',          # Vendor Refund
}


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def _compute_total_edocs(self):
        for item in self:
            item.total_edocs = self.env['invoice.eletronic'].search_count(
                [('invoice_id', '=', item.id)])

    invoice_eletronic_ids = fields.One2many(
        'invoice.eletronic', 'invoice_id',
        u'Documentos Eletrônicos', readonly=True)
    invoice_model = fields.Char(
        string="Modelo de Fatura", related="product_document_id.code",
        readonly=True)
    total_edocs = fields.Integer(string="Total NFe",
                                 compute=_compute_total_edocs)
    internal_number = fields.Integer(
        'Invoice Number', readonly=True,
        states={'draft': [('readonly', False)]},
        help=u"""Unique number of the invoice, computed
            automatically when the invoice is created.""")

    @api.multi
    def action_view_edocs(self):
        if self.total_edocs == 1:
            dummy, act_id = self.env['ir.model.data'].get_object_reference(
                'br_account_einvoice', 'action_sped_base_eletronic_doc')
            dummy, view_id = self.env['ir.model.data'].get_object_reference(
                'br_account_einvoice', 'br_account_invoice_eletronic_form')
            vals = self.env['ir.actions.act_window'].browse(act_id).read()[0]
            vals['view_id'] = (view_id, u'sped.eletronic.doc.form')
            vals['views'][1] = (view_id, u'form')
            vals['views'] = [vals['views'][1], vals['views'][0]]
            edoc = self.env['invoice.eletronic'].search(
                [('invoice_id', '=', self.id)], limit=1)
            vals['res_id'] = edoc.id
            return vals
        else:
            dummy, act_id = self.env['ir.model.data'].get_object_reference(
                'br_account_einvoice', 'action_sped_base_eletronic_doc')
            vals = self.env['ir.actions.act_window'].browse(act_id).read()[0]
            return vals

    def _return_pdf_invoice(self, doc):
        return None

    def action_preview_danfe(self):

        docs = self.env['invoice.eletronic'].search(
            [('invoice_id', '=', self.id)])

        if not docs:
            raise UserError(u'Não existe um E-Doc relacionado à esta fatura')

        if len(docs) > 1:
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'invoice.eletronic.selection.wizard',
                'name': "Escolha a nota a ser impressa",
                'view_mode': 'form',
                'context': self.env.context,
                'target': 'new',
                }
        else:
            return self._action_preview_danfe(docs[0])

    def _action_preview_danfe(self, doc):

        report = self._return_pdf_invoice(doc)
        if not report:
            raise UserError(
                'Nenhum relatório implementado para este modelo de documento')
        if not isinstance(report, str):
            return report
        action = self.env.ref(report).report_action(doc)
        return action

    def _prepare_edoc_item_vals(self, line):
        vals = {
            'name': line.name,
            'product_id': line.product_id.id,
            'account_invoice_line_id': line.id,
            'tipo_produto': line.product_type,
            'cfop': line.cfop_id.code,
            'uom_id': line.uom_id.id,
            'quantidade': line.quantity,
            'preco_unitario': line.price_unit,
            'valor_bruto': line.valor_bruto,
            'desconto': line.valor_desconto,
            'valor_liquido': line.price_subtotal,
            'origem': line.icms_origem,
            'tributos_estimados': line.tributos_estimados,
            'ncm': line.fiscal_classification_id.code,
            'item_pedido_compra': line.item_pedido_compra,
            # - ICMS -
            'icms_cst': line.icms_cst,
            'icms_aliquota': line.icms_aliquota,
            'icms_tipo_base': line.icms_tipo_base,
            'icms_aliquota_reducao_base': line.icms_aliquota_reducao_base,
            'icms_base_calculo': line.icms_base_calculo,
            'icms_valor': line.icms_valor,
            # - ICMS ST -
            'icms_st_aliquota': line.icms_st_aliquota,
            'icms_st_aliquota_mva': line.icms_st_aliquota_mva,
            'icms_st_aliquota_reducao_base': line.\
            icms_st_aliquota_reducao_base,
            'icms_st_base_calculo': line.icms_st_base_calculo,
            'icms_st_valor': line.icms_st_valor,
            # - Simples Nacional -
            'icms_aliquota_credito': line.icms_aliquota_credito,
            'icms_valor_credito': line.icms_valor_credito,
            # - IPI -
            'ipi_cst': line.ipi_cst,
            'ipi_aliquota': line.ipi_aliquota,
            'ipi_base_calculo': line.ipi_base_calculo,
            'ipi_reducao_bc': line.ipi_reducao_bc,
            'ipi_valor': line.ipi_valor,
            # - II -
            'ii_base_calculo': line.ii_base_calculo,
            'ii_valor_despesas': line.ii_valor_despesas,
            'ii_valor': line.ii_valor,
            'ii_valor_iof': line.ii_valor_iof,
            # - PIS -
            'pis_cst': line.pis_cst,
            'pis_aliquota': abs(line.pis_aliquota),
            'pis_base_calculo': line.pis_base_calculo,
            'pis_valor': abs(line.pis_valor),
            'pis_valor_retencao':
            abs(line.pis_valor) if line.pis_valor < 0 else 0,
            # - COFINS -
            'cofins_cst': line.cofins_cst,
            'cofins_aliquota': abs(line.cofins_aliquota),
            'cofins_base_calculo': line.cofins_base_calculo,
            'cofins_valor': abs(line.cofins_valor),
            'cofins_valor_retencao':
            abs(line.cofins_valor) if line.cofins_valor < 0 else 0,
            # - ISSQN -
            'issqn_codigo': line.service_type_id.code,
            'issqn_aliquota': abs(line.issqn_aliquota),
            'issqn_base_calculo': line.issqn_base_calculo,
            'issqn_valor': abs(line.issqn_valor),
            'issqn_valor_retencao':
            abs(line.issqn_valor) if line.issqn_valor < 0 else 0,
            # - RETENÇÔES -
            'csll_base_calculo': line.csll_base_calculo,
            'csll_aliquota': abs(line.csll_aliquota),
            'csll_valor_retencao':
            abs(line.csll_valor) if line.csll_valor < 0 else 0,
            'irrf_base_calculo': line.irrf_base_calculo,
            'irrf_aliquota': abs(line.irrf_aliquota),
            'irrf_valor_retencao':
            abs(line.irrf_valor) if line.irrf_valor < 0 else 0,
            'inss_base_calculo': line.inss_base_calculo,
            'inss_aliquota': abs(line.inss_aliquota),
            'inss_valor_retencao':
            abs(line.inss_valor) if line.inss_valor < 0 else 0,
        }
        return vals

    def _prepare_edoc_vals(self, invoice, inv_lines, serie_id):
        num_controle = int(''.join([str(SystemRandom().randrange(9))
                                    for i in range(8)]))
        vals = {
            'name': invoice.number,
            'invoice_id': invoice.id,
            'code': invoice.number,
            'company_id': invoice.company_id.id,
            'state': 'draft',
            'tipo_operacao': TYPE2EDOC[invoice.type],
            'numero_controle': num_controle,
            'data_emissao': datetime.now(),
            'data_agendada': invoice.date_invoice,
            'data_fatura': datetime.now(),
            'finalidade_emissao': '1',
            'partner_id': invoice.partner_id.id,
            'payment_term_id': invoice.payment_term_id.id,
            'fiscal_position_id': invoice.fiscal_position_id.id,
            'valor_icms': invoice.icms_value,
            'valor_icmsst': invoice.icms_st_value,
            'valor_ipi': invoice.ipi_value,
            'valor_pis': invoice.pis_value,
            'valor_cofins': invoice.cofins_value,
            'valor_ii': invoice.ii_value,
            'valor_bruto': invoice.total_bruto,
            'valor_desconto': invoice.total_desconto,
            'valor_final': invoice.amount_total,
            'valor_bc_icms': invoice.icms_base,
            'valor_bc_icmsst': invoice.icms_st_base,
            'valor_servicos': invoice.issqn_base,
            'valor_bc_issqn': invoice.issqn_base,
            'valor_issqn': invoice.issqn_value,
            'valor_estimado_tributos': invoice.total_tributos_estimados,
            'valor_retencao_issqn': invoice.issqn_retention,
            'valor_retencao_pis': invoice.pis_retention,
            'valor_retencao_cofins': invoice.cofins_retention,
            'valor_bc_irrf': invoice.irrf_base,
            'valor_retencao_irrf': invoice.irrf_retention,
            'valor_bc_csll': invoice.csll_base,
            'valor_retencao_csll': invoice.csll_retention,
            'valor_bc_inss': invoice.inss_base,
            'valor_retencao_inss': invoice.inss_retention,
        }

        total_produtos = total_servicos = 0.0
        eletronic_items = []
        for inv_line in inv_lines:
            if inv_line.product_type == 'service':
                total_servicos += inv_line.valor_bruto
            else:
                total_produtos += inv_line.valor_bruto
            eletronic_items.append((0, 0,
                                    self._prepare_edoc_item_vals(inv_line)))

        vals.update({
            'eletronic_item_ids': eletronic_items,
            'valor_servicos': total_servicos,
            'valor_bruto': total_produtos,
        })
        return vals

    @api.multi
    def invoice_validate(self):
        res = super(AccountInvoice, self).invoice_validate()
        for item in self:
            if item.product_document_id.electronic:
                if item.company_id.l10n_br_nfse_conjugada:
                    inv_lines = item.invoice_line_ids
                else:
                    inv_lines = item.invoice_line_ids.filtered(
                        lambda x: x.product_id.fiscal_type == 'product')
                if inv_lines:
                    edoc_vals = self._prepare_edoc_vals(
                        item, inv_lines, item.product_serie_id)
                    eletronic = self.env['invoice.eletronic'].create(edoc_vals)
                    eletronic.validate_invoice()
                    eletronic.action_post_validate()

            if item.service_document_id.nfse_eletronic and \
               not item.company_id.l10n_br_nfse_conjugada:
                inv_lines = item.invoice_line_ids.filtered(
                    lambda x: x.product_id.fiscal_type == 'service')
                if inv_lines:
                    edoc_vals = self._prepare_edoc_vals(
                        item, inv_lines, item.service_serie_id)
                    eletronic = self.env['invoice.eletronic'].create(edoc_vals)
                    eletronic.validate_invoice()
                    eletronic.action_post_validate()
        return res

    @api.multi
    def action_cancel(self):
        res = super(AccountInvoice, self).action_cancel()
        for item in self:
            edocs = self.env['invoice.eletronic'].search(
                [('invoice_id', '=', item.id)])
            for edoc in edocs:
                if edoc.state == 'done':
                    raise UserError(u'Documento eletrônico emitido - Cancele o \
                                    documento para poder cancelar a fatura')
                if edoc.can_unlink():
                    edoc.sudo().unlink()
        return res


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    state = fields.Selection(
        string="Status",
        selection=[
            ('pendente', 'Pendente'),
            ('transmitido', 'Transmitido'),
        ],
        default='pendente',
        help="""Define a situação eletrônica do item da fatura.
                Pendente: Ainda não foi transmitido eletronicamente.
                Transmitido: Já foi transmitido eletronicamente."""
    )

    item_pedido_compra = fields.Char(
        string=u'Item do pedido de compra do cliente')
