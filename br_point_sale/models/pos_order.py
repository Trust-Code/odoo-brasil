# -*- coding: utf-8 -*-
# © 2016 Alessandro Fernandes Martini <alessandrofmartini@gmail.com>, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from datetime import datetime
from random import SystemRandom
from odoo import api, models, fields


class PosOrder(models.Model):
    _inherit = 'pos.order'

    numero_controle = fields.Integer()

#    total_bruto = fields.Float() TODO
#    total_without_tax = fields.Float() TODO
#    total_tax = fields.Float() TODO
#    total_desconto = fields.Float() TODO

    @api.model
    def _process_order(self, pos_order):
        num_controle = int(''.join([str(SystemRandom().randrange(9))
                           for i in range(8)]))
        res = super(PosOrder, self)._process_order(pos_order)
        res.numero_controle = str(num_controle)
        foo = self._prepare_edoc_vals(res)
        eletronic = self.env['invoice.eletronic'].create(foo)
        eletronic.action_post_validate()
        return res

    def _prepare_edoc_item_vals(self, pos_line):
        values = pos_line.order_id.fiscal_position_id.map_tax_extra_values(
            pos_line.company_id, pos_line.product_id,
            pos_line.order_id.partner_id)
        tax_ids = [values.get('tax_icms_id', False),
                   values.get('tax_icms_st_id', False),
                   values.get('tax_ipi_id', False),
                   values.get('tax_pis_id', False),
                   values.get('tax_cofins_id', False),
                   values.get('tax_ii_id', False),
                   values.get('tax_issqn_id', False)]
        pos_line.update({
            'tax_ids': [(6, None, [x.id for x in tax_ids if x])]
        })
        vals = {
            'name': pos_line.name,
            'product_id': pos_line.product_id.id,
            'tipo_produto': pos_line.product_id.fiscal_type,
            'cfop': values['cfop_id'].code if values.get('cfop_id',
                                                         False) else False,
            'cest': pos_line.product_id.cest or
            pos_line.product_id.fiscal_classification_id.cest or '',
            'uom_id': pos_line.product_id.uom_id.id,
            'ncm': pos_line.product_id.fiscal_classification_id.code,
            'quantidade': pos_line.qty,
            'preco_unitario': pos_line.price_unit,
            'valor_bruto': pos_line.price_subtotal_incl,
            'valor_liquido': pos_line.price_subtotal,
            'origem': pos_line.product_id.origin,
            'tributos_estimados': (
                pos_line.price_subtotal_incl - pos_line.price_subtotal),
            # - ICMS -
            'icms_cst': values.get('icms_cst_normal', False),
            'icms_aliquota': 0,
            'icms_tipo_base': '3',
            'icms_aliquota_reducao_base': values.get(
                'icms_aliquota_reducao_base', False),
            'icms_base_calculo': pos_line.price_subtotal_incl,
            'icms_valor': 0,
            # - ICMS ST -
            'icms_st_aliquota': 0,
            'icms_st_aliquota_mva': 0,
            'icms_st_aliquota_reducao_base': 0,
            'icms_st_base_calculo': 0,
            'icms_st_valor': 0,
            # - Simples Nacional -
            'icms_aliquota_credito': 0,
            'icms_valor_credito': 0,
            # - IPI -
            'classe_enquadramento': '',
            'codigo_enquadramento': '999',
            'ipi_cst': '99' or values.get('ipi_cst', False),
            'ipi_aliquota': 0,
            'ipi_base_calculo': 0,
            'ipi_reducao_bc': 0,
            'ipi_valor': 0,
            # - II -
            'ii_base_calculo': 0,
            'ii_valor_despesas': 0,
            'ii_valor': 0,
            'ii_valor_iof': 0,
            # - PIS -
            'pis_cst': values.get('pis_cst', False),
            'pis_aliquota': 0,
            'pis_base_calculo': 0,
            'pis_valor': 0,
            # - COFINS -
            'cofins_cst': values['cofins_cst'],
            'cofins_aliquota': 0,
            'cofins_base_calculo': 0,
            'cofins_valor': 0,
            # - ISSQN -
            'issqn_codigo': 0,
            'issqn_aliquota': 0,
            'issqn_base_calculo': 0,
            'issqn_valor': 0,
            'issqn_valor_retencao': 0.00,

        }
        return vals

    def _prepare_edoc_vals(self, pos):
        vals = {
            'code': pos.sequence_number,
            'name': u'Documento Eletrônico: nº %d' % pos.sequence_number,
            'company_id': pos.company_id.id,
            'state': 'draft',
            'tipo_operacao': 'saida',
            'model': '65',
            'serie': 1,
            'numero': pos.sequence_number,
            'numero_controle': pos.numero_controle,
            'numero_nfe': pos.sequence_number,
            'data_emissao': datetime.now(),
            'data_fatura': datetime.now(),
            'finalidade_emissao': '1',
            'partner_id': pos.partner_id.id,
            'payment_term_id': None,
            'fiscal_position_id': 1,
        }

        eletronic_items = []
        for pos_line in pos.lines:
            eletronic_items.append((0, 0,
                                    self._prepare_edoc_item_vals(pos_line)))

        vals['eletronic_item_ids'] = eletronic_items
        vals['valor_icms'] = 30
        vals['valor_ipi'] = 0
        vals['valor_pis'] = 0
        vals['valor_cofins'] = 0
        vals['valor_ii'] = 0
        vals['valor_bruto'] = pos.amount_total - pos.amount_tax
        vals['valor_desconto'] = pos.amount_tax
        vals['valor_final'] = pos.amount_total
        vals['valor_bc_icms'] = 0
        vals['valor_bc_icmsst'] = 0
        return vals

    @api.multi
    def _compute_total_edocs(self):
        for item in self:
            item.total_edocs = self.env['invoice.eletronic'].search_count(
                [('numero_controle', '=', self.numero_controle)])

    total_edocs = fields.Integer(string="Total NFe",
                                 compute=_compute_total_edocs)

    @api.multi
    def action_view_edocs(self):
        if self.total_edocs == 1:
            edoc = self.env['invoice.eletronic'].search(
                [('numero_controle', '=', self.numero_controle)], limit=1)
            dummy, act_id = self.env['ir.model.data'].get_object_reference(
                'br_account_einvoice', 'action_sped_base_eletronic_doc')
            dummy, view_id = self.env['ir.model.data'].get_object_reference(
                'br_account_einvoice', 'sped_base_eletronic_doc_form')
            vals = self.env['ir.actions.act_window'].browse(act_id).read()[0]
            vals['view_id'] = (view_id, u'sped.eletronic.doc.form')
            vals['views'][1] = (view_id, u'form')
            vals['views'] = [vals['views'][1], vals['views'][0]]
            vals['res_id'] = edoc.id
            vals['search_view'] = False
            return vals
        else:
            dummy, act_id = self.env['ir.model.data'].get_object_reference(
                'br_account_einvoice', 'action_sped_base_eletronic_doc')
            vals = self.env['ir.actions.act_window'].browse(act_id).read()[0]
            return vals

