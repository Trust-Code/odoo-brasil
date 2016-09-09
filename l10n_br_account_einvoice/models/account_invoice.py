# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import api, fields, models
from datetime import datetime
from errno import ECOMM


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def _compute_total_edocs(self):
        for item in self:
            item.total_edocs = self.env['invoice.eletronic'].search_count(
                [('invoice_id', '=', item.id)])

    total_edocs = fields.Integer(string="Total NFe",
                                 compute=_compute_total_edocs)

    def _prepare_edoc_item_vals(self, invoice_line):
        vals = {
            'name': invoice_line.name,
            'product_id': invoice_line.product_id.id,
            'cfop': invoice_line.cfop_id.code,
            'uom_id': invoice_line.uom_id.id,
            'quantity': invoice_line.quantity,
            'unit_price': invoice_line.price_unit,
            'freight_value': invoice_line.freight_value,
            'insurance_value': invoice_line.insurance_value,
            'discount': invoice_line.discount_value,
            'other_expenses': invoice_line.other_costs_value,
            'gross_total': invoice_line.price_subtotal,
            'total': invoice_line.price_subtotal,
            'origem': invoice_line.icms_origin,
            'icms_cst': invoice_line.icms_cst,
            'icms_percentual_credit': invoice_line.icms_percent_credit,
            'icms_value_credit': invoice_line.icms_value_credit

        }

        return vals

    def _prepare_edoc_vals(self, invoice):
        vals = {
            'invoice_id': invoice.id,
            'code': invoice.number,
            'name': u'Documento Eletrônico: nº %d' % invoice.internal_number,
            'company_id': invoice.company_id.id,
            'state': 'draft',
            'tipo_operacao': 'saida',
            'model': '55',
            'serie': invoice.document_serie_id.id,
            'numero': invoice.internal_number,
            'numero_controle': invoice.internal_number,
            'data_emissao': datetime.now(),
            'data_fatura': datetime.now(),
            'ambiente': 'homologacao',
            'finalidade_emissao': '1',
            'consumidor_final': invoice.ind_final,
            'partner_id': invoice.partner_id.id,
            'partner_shipping_id': invoice.partner_shipping_id.id,
            'payment_term_id': invoice.payment_term_id.id,
            'fiscal_position_id': invoice.fiscal_position_id.id,
        }

        eletronic_items = []
        total_sum = float()
        total_frete = float()
        total_seguro = float()
        total_desconto = float()
        total_despesas = float()
        total_icms = sum([tax.amount for tax in invoice.tax_line_ids.filtered(
            lambda x: x.tax_id.domain == 'simples')])
        total_ipi = sum([tax.amount for tax in invoice.tax_line_ids.filtered(
            lambda x: x.tax_id.domain == 'ipi')])
        total_pis = sum([tax.amount for tax in invoice.tax_line_ids.filtered(
            lambda x: x.tax_id.domain == 'pis')])
        total_cofins = sum(
            [tax.amount for tax in invoice.tax_line_ids.filtered(
                lambda x: x.tax_id.domain == 'cofins')])
        for inv_line in invoice.invoice_line_ids:
            eletronic_items.append((0, 0,
                                    self._prepare_edoc_item_vals(inv_line)))
            total_sum += inv_line.price_total
            total_frete += inv_line.freight_value
            total_seguro += inv_line.insurance_value
            total_desconto += (inv_line.price_total
                               / (1 - inv_line.discount / 100)) - total_sum
            total_despesas += inv_line.other_costs_value

        vals['eletronic_item_ids'] = eletronic_items
        vals['valor_icms'] = total_icms
        vals['valor_ipi'] = total_ipi
        vals['valor_pis'] = total_pis
        vals['valor_cofins'] = total_cofins
        vals['valor_bruto'] = total_sum
        vals['valor_frete'] = total_frete
        vals['valor_seguro'] = total_seguro
        vals['valor_desconto'] = total_desconto
        vals['valor_final'] = total_sum + total_seguro + total_frete
        return vals

    @api.multi
    def invoice_validate(self):
        res = super(AccountInvoice, self).invoice_validate()
        self.action_number()
        for item in self:
            edoc_vals = self._prepare_edoc_vals(item)
            self.env['invoice.eletronic'].create(edoc_vals)
        return res

    @api.multi
    def action_cancel(self):
        res = super(AccountInvoice, self).action_cancel()
        for item in self:
            edocs = self.env['invoice.eletronic'].search(
                [('invoice_id', '=', item.id)])
            edocs.unlink()

        return res
