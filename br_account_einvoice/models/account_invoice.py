# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro <danimaribeiro@gmail.com>, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from datetime import datetime
from random import SystemRandom


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
            seq_number = \
                invoice.document_serie_id.internal_sequence_id.next_by_id()

            self.write(
                {'internal_number': seq_number})
        return True

    def _prepare_edoc_item_vals(self, invoice_line):
        vals = {
            'name': invoice_line.name,
            'product_id': invoice_line.product_id.id,
            'tipo_produto': invoice_line.product_type,
            'cfop': invoice_line.cfop_id.code,
            'uom_id': invoice_line.uom_id.id,
            'quantidade': invoice_line.quantity,
            'preco_unitario': invoice_line.price_unit,
            'seguro': invoice_line.valor_seguro,
            'desconto': invoice_line.valor_desconto,
            'outras_despesas': invoice_line.outras_despesas,
            'valor_bruto': invoice_line.valor_bruto,
            'valor_liquido': invoice_line.price_subtotal,
            'origem': invoice_line.icms_origem,
            'tributos_estimados': invoice_line.tributos_estimados,
            # - ICMS -
            'icms_cst': invoice_line.icms_cst,
            'icms_aliquota': invoice_line.icms_aliquota,
            'icms_tipo_base': invoice_line.icms_tipo_base,
            'icms_aliquota_reducao_base': invoice_line.icms_aliquota_reducao_base,
            'icms_base_calculo': invoice_line.icms_base_calculo,
            'icms_valor': invoice_line.icms_valor,
            # - ICMS ST -
            'icms_st_aliquota': invoice_line.icms_st_aliquota,
            'icms_st_aliquota_mva': invoice_line.icms_st_aliquota_mva,
            'icms_st_aliquota_reducao_base': invoice_line.icms_st_aliquota_reducao_base,
            'icms_st_base_calculo': invoice_line.icms_st_base_calculo,
            'icms_st_valor': invoice_line.icms_st_valor,
            # - Simples Nacional -
            'icms_aliquota_credito': invoice_line.icms_aliquota_credito,
            'icms_valor_credito': invoice_line.icms_valor_credito,
            # - IPI -
            'classe_enquadramento': '',
            'codigo_enquadramento': '999',
            'ipi_cst': invoice_line.ipi_cst,
            'ipi_aliquota': invoice_line.ipi_aliquota,
            'ipi_base_calculo': invoice_line.ipi_base_calculo,
            'ipi_reducao_bc': invoice_line.ipi_reducao_bc,
            'ipi_valor': invoice_line.ipi_valor,
            # - II -
            'ii_base_calculo': invoice_line.ii_base_calculo,
            'ii_valor_despesas': invoice_line.ii_valor_despesas,
            'ii_valor': invoice_line.ii_valor,
            'ii_valor_iof': invoice_line.ii_valor_iof,
            # - PIS -
            'pis_cst': invoice_line.pis_cst,
            'pis_aliquota': invoice_line.pis_aliquota,
            'pis_base_calculo': invoice_line.pis_base_calculo,
            'pis_valor': invoice_line.pis_valor,
            # - COFINS -
            'cofins_cst': invoice_line.cofins_cst,
            'cofins_aliquota': invoice_line.cofins_aliquota,
            'cofins_base_calculo': invoice_line.cofins_base_calculo,
            'cofins_valor': invoice_line.cofins_valor,
            # - ISSQN -
            'issqn_codigo': invoice_line.service_type_id.code,
            'issqn_aliquota': invoice_line.issqn_aliquota,
            'issqn_base_calculo': invoice_line.issqn_base_calculo,
            'issqn_valor': invoice_line.issqn_valor,
            'issqn_valor_retencao': 0.00,
        }

        return vals

    def _prepare_edoc_vals(self, invoice):
        num_NFe = str(invoice.internal_number).zfill(9)
        num_NFe = num_NFe[:3] + '.' + num_NFe[3:6] + '.' + num_NFe[6:9]
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
            'numero_controle': int(''.join([str(SystemRandom().randrange(9))
                                            for i in range(8)])),
            'numero_nfe': num_NFe,
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
