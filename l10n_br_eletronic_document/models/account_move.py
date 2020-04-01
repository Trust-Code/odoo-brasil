from datetime import datetime
from random import SystemRandom

from odoo import api, fields, models

TYPE2EDOC = {
    'out_invoice': 'saida',        # Customer Invoice
    'in_invoice': 'entrada',          # Vendor Bill
    'out_refund': 'entrada',        # Customer Refund
    'in_refund': 'saida',          # Vendor Refund
}


class AccountMove(models.Model):
    _inherit = 'account.move'

    def _compute_total_edocs(self):
        for item in self:
            item.total_edocs = self.env['eletronic.document'].search_count(
                [('move_id', '=', item.id)])

    total_edocs = fields.Integer(string="Total NFe", compute=_compute_total_edocs)

    l10n_br_edoc_policy = fields.Selection(
        [('directly', 'Emitir agora'),
         ('after_payment', 'Emitir após pagamento'),
         ('manually', 'Manualmente')], string="Nota Eletrônica", default='directly')

    def _prepare_eletronic_line_vals(self, invoice_lines):
        lines = []
        for line in invoice_lines:
            vals = {
                'name': line.name,
                'product_id': line.product_id.id,
                'eletronic_document_id': line.id,
                'tipo_produto': 'service' if line.product_id.type == 'service' else 'product',
                # 'cfop': line.cfop_id.code,
                'uom_id': line.product_uom_id.id,
                'quantidade': line.quantity,
                'preco_unitario': line.price_unit,
                'valor_bruto': line.price_subtotal,
                # 'desconto': line.valor_desconto,
                'valor_liquido': line.price_total,
                # 'origem': line.icms_origem,
                #  'tributos_estimados': line.tributos_estimados,
                # 'ncm': line.fiscal_classification_id.code,
                'pedido_compra': self.ref,
                # 'item_pedido_compra': line.item_pedido_compra,
                # - ICMS -
                # 'icms_cst': line.icms_cst,
                # 'icms_aliquota': line.icms_aliquota,
                # 'icms_tipo_base': line.icms_tipo_base,
                # 'icms_aliquota_reducao_base': line.icms_aliquota_reducao_base,
                # 'icms_base_calculo': line.icms_base_calculo,
                # 'icms_valor': line.icms_valor,
                # - ICMS ST -
                # 'icms_st_aliquota': line.icms_st_aliquota,
                # 'icms_st_aliquota_mva': line.icms_st_aliquota_mva,
                # 'icms_st_aliquota_reducao_base': line.\
                # icms_st_aliquota_reducao_base,
                # 'icms_st_base_calculo': line.icms_st_base_calculo,
                # 'icms_st_valor': line.icms_st_valor,
                # # - Simples Nacional -
                # 'icms_aliquota_credito': line.icms_aliquota_credito,
                # 'icms_valor_credito': line.icms_valor_credito,
                # - IPI -
                # 'ipi_cst': line.ipi_cst,
                # 'ipi_aliquota': line.ipi_aliquota,
                # 'ipi_base_calculo': line.ipi_base_calculo,
                # 'ipi_reducao_bc': line.ipi_reducao_bc,
                # 'ipi_valor': line.ipi_valor,
                # - II -
                # 'ii_base_calculo': line.ii_base_calculo,
                # 'ii_valor_despesas': line.ii_valor_despesas,
                # 'ii_valor': line.ii_valor,
                # 'ii_valor_iof': line.ii_valor_iof,
                # - PIS -
                # 'pis_cst': line.pis_cst,
                # 'pis_aliquota': abs(line.pis_aliquota),
                # 'pis_base_calculo': line.pis_base_calculo,
                # 'pis_valor': abs(line.pis_valor),
                # 'pis_valor_retencao':
                # abs(line.pis_valor) if line.pis_valor < 0 else 0,
                # - COFINS -
                # 'cofins_cst': line.cofins_cst,
                # 'cofins_aliquota': abs(line.cofins_aliquota),
                # 'cofins_base_calculo': line.cofins_base_calculo,
                # 'cofins_valor': abs(line.cofins_valor),
                # 'cofins_valor_retencao':
                # abs(line.cofins_valor) if line.cofins_valor < 0 else 0,
                # - ISSQN -
                # 'issqn_codigo': line.service_type_id.code,
                # 'issqn_aliquota': abs(line.issqn_aliquota),
                # 'issqn_base_calculo': line.issqn_base_calculo,
                # 'issqn_valor': abs(line.issqn_valor),
                # 'issqn_valor_retencao':
                # abs(line.issqn_valor) if line.issqn_valor < 0 else 0,
                # - RETENÇÔES -
                # 'csll_base_calculo': line.csll_base_calculo,
                # 'csll_aliquota': abs(line.csll_aliquota),
                # 'csll_valor_retencao':
                # abs(line.csll_valor) if line.csll_valor < 0 else 0,
                # 'irrf_base_calculo': line.irrf_base_calculo,
                # 'irrf_aliquota': abs(line.irrf_aliquota),
                # 'irrf_valor_retencao':
                # abs(line.irrf_valor) if line.irrf_valor < 0 else 0,
                # 'inss_base_calculo': line.inss_base_calculo,
                # 'inss_aliquota': abs(line.inss_aliquota),
                # 'inss_valor_retencao':
                # abs(line.inss_valor) if line.inss_valor < 0 else 0,
            }
            lines.append((0, 0, vals))

        return lines

    def _prepare_eletronic_doc_vals(self):
        invoice = self
        num_controle = int(''.join([str(SystemRandom().randrange(9))
                                    for i in range(8)]))
        vals = {
            'name': invoice.name,
            'move_id': invoice.id,
            'company_id': invoice.company_id.id,
            'schedule_user_id': self.env.user.id,
            'state': 'draft',
            'tipo_operacao': TYPE2EDOC[invoice.type],
            'numero_controle': num_controle,
            'data_emissao': datetime.now(),
            'data_agendada': invoice.invoice_date,
            'finalidade_emissao': '1',
            'partner_id': invoice.partner_id.id,
            'payment_term_id': invoice.invoice_payment_term_id.id,
            'fiscal_position_id': invoice.fiscal_position_id.id,
            # 'valor_icms': invoice.icms_value,
            # 'valor_icmsst': invoice.icms_st_value,
            # 'valor_ipi': invoice.ipi_value,
            # 'valor_pis': invoice.pis_value,
            # 'valor_cofins': invoice.cofins_value,
            # 'valor_ii': invoice.ii_value,
            'valor_bruto': invoice.amount_total,
            # 'valor_desconto': invoice.total_desconto,
            'valor_final': invoice.amount_total,
            # 'valor_bc_icms': invoice.icms_base,
            # 'valor_bc_icmsst': invoice.icms_st_base,
            # 'valor_bc_issqn': invoice.issqn_base,
            # 'valor_issqn': invoice.issqn_value,
            # 'valor_estimado_tributos': invoice.total_tributos_estimados,
            # 'valor_retencao_issqn': invoice.issqn_retention,
            # 'valor_retencao_pis': invoice.pis_retention,
            # 'valor_retencao_cofins': invoice.cofins_retention,
            # 'valor_bc_irrf': invoice.irrf_base,
            # 'valor_retencao_irrf': invoice.irrf_retention,
            # 'valor_bc_csll': invoice.csll_base,
            # 'valor_retencao_csll': invoice.csll_retention,
            # 'valor_bc_inss': invoice.inss_base,
            # 'valor_retencao_inss': invoice.inss_retention,
        }

        total_produtos = total_servicos = 0.0
        for inv_line in self.invoice_line_ids:
            if inv_line.product_id.type == 'service':
                total_servicos += inv_line.price_subtotal
            else:
                total_produtos += inv_line.price_subtotal

        vals.update({
            'valor_servicos': total_servicos,
            'valor_produtos': total_produtos,
        })
        return vals

    def action_create_eletronic_document(self):
        for move in self:
            vals = move._prepare_eletronic_doc_vals()
            services = move.invoice_line_ids.filtered(lambda  x: x.product_id.type == 'service')
            if services:
                vals['model'] = 'nfse'
                vals['document_line_ids'] = self._prepare_eletronic_line_vals(services)
                self.env['eletronic.document'].create(vals)
            products = move.invoice_line_ids.filtered(lambda  x: x.product_id.type != 'service')
            if products:
                vals['model'] = 'nfe'
                vals['document_line_ids'] = self._prepare_eletronic_line_vals(products)
                self.env['eletronic.document'].create(vals)

    def action_post(self):
        res = super(AccountMove, self).action_post()
        moves = self.filtered(lambda x: x.l10n_br_edoc_policy == 'directly' and x.type != 'entry')
        moves.action_create_eletronic_document()
        return res

    def action_view_edocs(self):
        if self.total_edocs == 1:
            dummy, act_id = self.env['ir.model.data'].get_object_reference(
                'l10n_br_eletronic_document', 'action_view_eletronic_document')
            dummy, view_id = self.env['ir.model.data'].get_object_reference(
                'l10n_br_eletronic_document', 'view_eletronic_document_form')
            vals = self.env['ir.actions.act_window'].browse(act_id).read()[0]
            vals['view_id'] = (view_id, 'sped.eletronic.doc.form')
            vals['views'][1] = (view_id, 'form')
            vals['views'] = [vals['views'][1], vals['views'][0]]
            edoc = self.env['eletronic.document'].search(
                [('move_id', '=', self.id)], limit=1)
            vals['res_id'] = edoc.id
            return vals
        else:
            dummy, act_id = self.env['ir.model.data'].get_object_reference(
                'l10n_br_eletronic_document', 'action_view_eletronic_document')
            vals = self.env['ir.actions.act_window'].browse(act_id).read()[0]
            vals['domain'] = [('move_id', '=', self.id)]
            return vals
