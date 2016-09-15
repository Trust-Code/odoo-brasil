# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro <danimaribeiro@gmail.com>, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from datetime import datetime


from odoo import api, fields, models
from odoo.exceptions import UserError


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def _compute_total_edocs(self):
        for item in self:
            item.total_edocs = self.env['invoice.eletronic'].search_count(
                [('invoice_id', '=', item.id)])

    total_edocs = fields.Integer(string="Total NFe",
                                 compute=_compute_total_edocs)

    internal_number = fields.Integer(
        'Invoice Number', readonly=True,
        states={'draft': [('readonly', False)]},
        help="""Unique number of the invoice, computed
            automatically when the invoice is created.""")

    @api.multi
    def action_view_edocs(self):
        if self.total_edocs == 1:
            dummy, act_id = self.env['ir.model.data'].get_object_reference(
                'br_account_einvoice', 'action_sped_base_eletronic_doc')
            dummy, view_id = self.env['ir.model.data'].get_object_reference(
                'br_account_einvoice', 'sped_base_eletronic_doc_form')
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

    @api.multi
    def action_number(self):
        for invoice in self:
            if not invoice.document_serie_id.internal_sequence_id.id:
                raise UserError(
                    u'Configure a sequência para a numeração da nota')
            sequence_obj = self.env['ir.sequence']
            seq_number = sequence_obj.get_id(
                invoice.document_serie_id.internal_sequence_id.id)

            self.write(
                {'internal_number': seq_number})
        return True

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
            'model': invoice.fiscal_document_id.code,
            'serie': invoice.document_serie_id.id,
            'numero': invoice.internal_number,
            'numero_controle': invoice.internal_number,
            'data_emissao': datetime.now(),
            'data_fatura': datetime.now(),
            'finalidade_emissao': '1',
            'partner_id': invoice.partner_id.id,
            'partner_shipping_id': invoice.partner_shipping_id.id,
            'payment_term_id': invoice.payment_term_id.id,
            'fiscal_position_id': invoice.fiscal_position_id.id,
        }

        eletronic_items = []
        for inv_line in invoice.invoice_line_ids:
            eletronic_items.append((0, 0,
                                    self._prepare_edoc_item_vals(inv_line)))

        vals['eletronic_item_ids'] = eletronic_items
        vals['valor_icms'] = invoice.icms_value
        vals['valor_ipi'] = invoice.ipi_value
        vals['valor_pis'] = invoice.pis_value
        vals['valor_cofins'] = invoice.cofins_value
        vals['valor_ii'] = invoice.ii_value
        vals['valor_bruto'] = invoice.amount_gross
        vals['valor_seguro'] = invoice.amount_insurance
        vals['valor_desconto'] = invoice.amount_discount
        vals['valor_final'] = invoice.amount_total
        return vals

    @api.multi
    def invoice_validate(self):
        res = super(AccountInvoice, self).invoice_validate()
        self.action_number()
        for item in self:
            if item.is_eletronic:
                edoc_vals = self._prepare_edoc_vals(item)
                if edoc_vals:
                    eletronic = self.env['invoice.eletronic'].create(edoc_vals)
                    eletronic.validate_invoice()
        return res

    @api.multi
    def action_cancel(self):
        res = super(AccountInvoice, self).action_cancel()
        for item in self:
            edocs = self.env['invoice.eletronic'].search(
                [('invoice_id', '=', item.id)])
            edocs.unlink()

        return res
