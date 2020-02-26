# -*- coding: utf-8 -*-
# © 2016 Alessandro Fernandes Martini <alessandrofmartini@gmail.com>, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from datetime import datetime
from random import SystemRandom
from odoo.addons import decimal_precision as dp
from odoo import api, models, fields
from odoo.exceptions import UserError


class PosOrder(models.Model):
    _inherit = 'pos.order'

    @api.multi
    def _compute_nfe_number(self):
        for item in self:
            docs = self.env['invoice.eletronic'].search(
                [('pos_order_id', '=', item.id)])
            if docs:
                item.nfe_number = docs[0].numero
                item.nfe_exception_number = docs[0].numero
                item.nfe_exception = (docs[0].state in ('error', 'denied'))
                item.sending_nfe = docs[0].state == 'draft'
                item.nfe_status = '%s - %s' % (
                    docs[0].codigo_retorno, docs[0].mensagem_retorno)

    ambiente_nfe = fields.Selection(
        string="Ambiente NFe", related="company_id.tipo_ambiente",
        readonly=True)
    sending_nfe = fields.Boolean(
        string="Enviando NFe?", compute="_compute_nfe_number")
    nfe_exception = fields.Boolean(
        string="Problemas na NFe?", compute="_compute_nfe_number")
    nfe_status = fields.Char(
        string="Mensagem NFe", compute="_compute_nfe_number")
    nfe_number = fields.Integer(
        string=u"Número NFe", compute="_compute_nfe_number")
    nfe_exception_number = fields.Integer(
        string=u"Número NFe", compute="_compute_nfe_number")
    numero_controle = fields.Integer()
    customer_cpf = fields.Char(string="CPF cliente")

    @api.depends('statement_ids', 'lines')
    def _compute_amount_taxes(self):
        for order in self:
            order.total_icms = sum(line.valor_icms for line in order.lines)
            order.total_pis = sum(line.valor_pis for line in order.lines)
            order.total_cofins = sum(line.valor_pis for line in order.lines)

    @api.model
    def _order_fields(self, ui_order):
        res = super(PosOrder, self)._order_fields(ui_order)
        res.update({'customer_cpf': ui_order['customer_cpf'] or False})
        return res

    def action_preview_danfe(self):
        docs = self.env['invoice.eletronic'].search(
            [('pos_order_id', '=', self.id)])

        if not docs:
            raise UserError(u'Não existe um E-Doc relacionado à este pedido')

        for doc in docs:
            if doc.state == 'draft':
                raise UserError(
                    'Nota Fiscal de consumidor na fila de envio. Aguarde!')

        action = self.env.ref('br_nfe.report_br_nfe_danfe').report_action(docs)
        return action

    @api.model
    def _process_order(self, pos_order):
        num_controle = int(''.join([str(SystemRandom().randrange(9))
                                    for i in range(8)]))

        res = super(PosOrder, self)._process_order(pos_order)
        res.numero_controle = str(num_controle)

        if not res.fiscal_position_id:
            res.fiscal_position_id = \
                res.session_id.config_id.default_fiscal_position_id.id

        res.numero = \
            res.fiscal_position_id.product_serie_id.\
            internal_sequence_id.next_by_id()

        for line in res.lines:
            values = line.order_id.fiscal_position_id.map_tax_extra_values(
                line.company_id, line.product_id,
                line.order_id.partner_id)

            empty = self.env['account.tax'].browse()
            tax_ids = values.get('tax_icms_id', empty) | \
                values.get('tax_icms_st_id', empty) | \
                values.get('tax_icms_inter_id', empty) | \
                values.get('tax_icms_intra_id', empty) | \
                values.get('tax_icms_fcp_id', empty) | \
                values.get('tax_ipi_id', empty) | \
                values.get('tax_pis_id', empty) | \
                values.get('tax_cofins_id', empty) | \
                values.get('tax_ii_id', empty) | \
                values.get('tax_issqn_id', empty)

            other_taxes = line.tax_ids.filtered(lambda x: not x.domain)
            tax_ids |= other_taxes
            line.update({
                'tax_ids': [(6, None, [x.id for x in tax_ids if x])]
            })

            for key, value in values.items():
                if value and key in line._fields:
                    line.update({key: value})
        foo = self._prepare_edoc_vals(res)
        eletronic = self.env['invoice.eletronic'].create(foo)
        eletronic.validate_invoice()
        eletronic.action_post_validate()
        return res

    def _prepare_edoc_item_vals(self, pos_line):
        vals = {
            'name': pos_line.name,
            'product_id': pos_line.product_id.id,
            'tipo_produto': pos_line.product_id.fiscal_type,
            'cfop': pos_line.cfop_id.code,
            'cest': pos_line.product_id.cest or
            pos_line.product_id.fiscal_classification_id.cest or '',
            'uom_id': pos_line.product_id.uom_id.id,
            'ncm': pos_line.product_id.fiscal_classification_id.code,
            'quantidade': pos_line.qty,
            'preco_unitario': pos_line.price_unit,
            'valor_bruto': pos_line.price_subtotal_incl,
            'valor_liquido': pos_line.price_subtotal,
            'origem': pos_line.product_id.origin,
            'tributos_estimados': pos_line.get_approximate_taxes(),
            # - ICMS -
            'icms_cst': pos_line.icms_cst_normal or \
            pos_line.icms_csosn_simples,
            'icms_aliquota': pos_line.aliquota_icms,
            'icms_tipo_base': '3',
            'icms_aliquota_reducao_base': pos_line.icms_aliquota_reducao_base,
            'icms_base_calculo': pos_line.base_icms,
            'icms_valor': pos_line.valor_icms,
            # - ICMS ST -
            'icms_st_aliquota': 0,
            'icms_st_aliquota_mva': 0,
            'icms_st_aliquota_reducao_base': pos_line.\
            icms_st_aliquota_reducao_base,
            'icms_st_base_calculo': 0,
            'icms_st_valor': 0,
            # - Simples Nacional -
            'icms_aliquota_credito': 0,
            'icms_valor_credito': 0,
            # - II -
            'ii_base_calculo': 0,
            'ii_valor_despesas': 0,
            'ii_valor': 0,
            'ii_valor_iof': 0,
            # - IPI -
            'ipi_cst': pos_line.ipi_cst,
            'ipi_aliquota': pos_line.aliquota_ipi,
            'ipi_base_calculo': pos_line.base_ipi,
            'ipi_valor': pos_line.valor_ipi,
            # - PIS -
            'pis_cst': pos_line.pis_cst,
            'pis_aliquota': pos_line.aliquota_pis,
            'pis_base_calculo': pos_line.base_pis,
            'pis_valor': pos_line.valor_pis,
            # - COFINS -
            'cofins_cst': pos_line.cofins_cst,
            'cofins_aliquota': pos_line.aliquota_cofins,
            'cofins_base_calculo': pos_line.base_cofins,
            'cofins_valor': pos_line.valor_cofins,
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
            'pos_order_id': pos.id,
            'code': pos.sequence_number,
            'name': u'Documento Eletrônico: nº %d' % pos.sequence_number,
            'company_id': pos.company_id.id,
            'state': 'draft',
            'tipo_operacao': 'saida',
            'model': '65',
            'ind_dest': '1',
            'ind_ie_dest': '9',
            'ambiente': 'homologacao'
            if pos.company_id.tipo_ambiente == '2' else 'producao',
            'serie': pos.fiscal_position_id.product_serie_id.id,
            'numero': pos.numero,
            'numero_nfe': pos.numero,
            'numero_controle': pos.numero_controle,
            'data_emissao': datetime.now(),
            'data_fatura': datetime.now(),
            'finalidade_emissao': '1',
            'partner_id': pos.partner_id.id,
            'customer_cpf': pos.customer_cpf,
            'payment_term_id': None,
            'fiscal_position_id': pos.fiscal_position_id.id,
            'ind_final': pos.fiscal_position_id.ind_final,
            'ind_pres': pos.fiscal_position_id.ind_pres,
            'metodo_pagamento': pos.statement_ids[0].journal_id.
            metodo_pagamento,
            'troco': abs(sum(
                payment.amount for payment in
                pos.statement_ids if payment.amount < 0)),
            'valor_pago': sum(
                payment.amount for payment in
                pos.statement_ids if payment.amount > 0)
            }

        base_icms = 0
        base_cofins = 0
        base_pis = 0
        eletronic_items = []
        for pos_line in pos.lines:
            eletronic_items.append((0, 0,
                                    self._prepare_edoc_item_vals(pos_line)))
            base_icms += pos_line.base_icms
            base_pis += pos_line.base_pis
            base_cofins += pos_line.base_cofins

        vals['valor_estimado_tributos'] = \
            self.get_total_tributes(eletronic_items)
        vals['eletronic_item_ids'] = eletronic_items
        vals['valor_icms'] = pos.total_icms
        vals['valor_pis'] = pos.total_pis
        vals['valor_cofins'] = pos.total_cofins
        vals['valor_ii'] = 0
        vals['valor_bruto'] = pos.amount_total - pos.amount_tax
        vals['valor_desconto'] = pos.amount_tax
        vals['valor_final'] = pos.amount_total
        vals['valor_bc_icms'] = base_icms
        vals['valor_bc_icmsst'] = 0
        return vals

    def get_total_tributes(self, values):
        trib = []
        for item in values:
            val = item[2].get('tributos_estimados')
            if val:
                trib.append(float(val))
        return sum(trib)

    @api.multi
    def _compute_total_edocs(self):
        for item in self:
            item.total_edocs = self.env['invoice.eletronic'].search_count(
                [('pos_order_id', '=', item.id)])

    total_edocs = fields.Integer(string="Total NFe",
                                 compute=_compute_total_edocs)

    @api.multi
    def action_view_edocs(self):
        if self.total_edocs == 1:
            edoc = self.env['invoice.eletronic'].search(
                [('pos_order_id', '=', self.id)], limit=1)
            dummy, act_id = self.env['ir.model.data'].get_object_reference(
                'br_account_einvoice', 'action_sped_base_eletronic_doc')
            dummy, view_id = self.env['ir.model.data'].get_object_reference(
                'br_account_einvoice', 'br_account_invoice_eletronic_form')
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

    @api.model
    def _amount_line_tax(self, line, fiscal_position_id):
        taxes = line.tax_ids.filtered(
            lambda t: t.company_id.id == line.order_id.company_id.id)
        if fiscal_position_id:
            taxes = fiscal_position_id.map_tax(
                taxes, line.product_id, line.order_id.partner_id)
        price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
        taxes = taxes.compute_all(
            price, line.order_id.pricelist_id.currency_id, line.qty,
            product=line.product_id,
            partner=line.order_id.partner_id or False)
        return taxes['total_included'] - taxes['total_excluded']

    total_icms = fields.Float(
        string='ICMS', compute=_compute_amount_taxes, store=True)
    total_pis = fields.Float(
        string='PIS', compute=_compute_amount_taxes, store=True)
    total_cofins = fields.Float(
        string='COFINS', compute=_compute_amount_taxes, store=True)


class PosOrderLine(models.Model):
    _inherit = 'pos.order.line'

    def _prepare_tax_context(self):
        return {
            'icms_st_aliquota_mva': self.icms_st_aliquota_mva,
            'icms_aliquota_reducao_base': self.icms_aliquota_reducao_base,
            'icms_st_aliquota_reducao_base':
            self.icms_st_aliquota_reducao_base,
            'icms_base_calculo': self.base_icms,
            'pis_base_calculo': self.base_pis,
            'cofins_base_calculo': self.base_cofins,
        }

    def get_approximate_taxes(self):
        ncm = self.product_id.fiscal_classification_id

        tributos_estimados_federais = self.price_subtotal * (
            ncm.federal_nacional / 100)
        tributos_estimados_estaduais = \
            self.price_subtotal * (ncm.estadual_imposto / 100)
        tributos_estimados_municipais = \
            self.price_subtotal * (ncm.municipal_imposto / 100)

        return "%.02f" % (
            tributos_estimados_federais +
            tributos_estimados_estaduais +
            tributos_estimados_municipais)

    @api.depends('price_unit', 'tax_ids', 'qty', 'discount', 'product_id')
    def _compute_amount_line_all(self):
        super(PosOrderLine, self)._compute_amount_line_all()
        for line in self:
            currency = line.order_id.pricelist_id.currency_id
            values = line.order_id.fiscal_position_id.map_tax_extra_values(
                line.company_id, line.product_id, line.order_id.partner_id)
            tax_ids = [values.get('tax_icms_id', False),
                       values.get('tax_icms_st_id', False),
                       values.get('tax_ipi_id', False),
                       values.get('tax_pis_id', False),
                       values.get('tax_cofins_id', False),
                       values.get('tax_ii_id', False),
                       values.get('tax_issqn_id', False)]

            line.update({
                'tax_ids': [(6, None, [x.id for x in tax_ids if x])]
            })
            line.cfop_id = values['cfop_id'].code if values.get(
                'cfop_id', False) else False
            line.icms_cst_normal = values.get('icms_cst_normal', False)
            line.icms_csosn_simples = values.get('icms_csosn_simples', False)
            line.icms_st_aliquota_mva = values.get('icms_st_aliquota_mva',
                                                   False)
            line.aliquota_icms_proprio = values.get('aliquota_icms_proprio',
                                                    False)
            line.incluir_ipi_base = values.get('incluir_ipi_base', False)
            line.icms_aliquota_reducao_base = values.get(
                'icms_aliquota_reducao_base', False)
            line.icms_st_aliquota_reducao_base = values.get(
                'icms_st_aliquota_reducao_base', False)
            line.ipi_cst = values.get('ipi_cst', False) or u'99'
            line.ipi_reducao_bc = values.get('ipi_reducao_bc', False)
            line.ipi_cst = values.get('ipi_cst', False)
            line.pis_cst = values.get('pis_cst', False)
            line.cofins_cst = values.get('cofins_cst', False)
            line.valor_bruto = line.qty * line.price_unit
            line.valor_desconto = line.valor_bruto * line.discount / 100
            taxes_ids = line.tax_ids.filtered(
                lambda tax: tax.company_id.id == line.order_id.
                company_id.id)
            fiscal_position_id = line.order_id.fiscal_position_id
            if fiscal_position_id:
                taxes_ids = fiscal_position_id.map_tax(
                    taxes_ids, line.product_id,
                    line.order_id.partner_id)
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            taxes = {'taxes': []}
            if taxes_ids:
                ctx = line._prepare_tax_context()
                taxes_ids = taxes_ids.with_context(**ctx)
                taxes = taxes_ids.compute_all(
                    price, currency, line.qty, product=line.product_id,
                    partner=line.order_id.partner_id or False)
            for tax in taxes['taxes']:
                tax_id = self.env['account.tax'].browse(tax['id'])
                if tax_id.domain == 'icms':
                    line.valor_icms = tax.get('amount', 0.00)
                    line.base_icms = tax.get('base', 0.00)
                    line.aliquota_icms = tax_id.amount
                if tax_id.domain == 'ipi':
                    line.valor_ipi = tax.get('amount', 0.00)
                    line.base_ipi = tax.get('base', 0.00)
                    line.aliquota_ipi = tax_id.amount
                if tax_id.domain == 'pis':
                    line.valor_pis = tax.get('amount', 0.00)
                    line.base_pis = tax.get('base', 0.00)
                    line.aliquota_pis = tax_id.amount
                if tax_id.domain == 'cofins':
                    line.valor_cofins = tax.get('amount', 0.00)
                    line.base_cofins = tax.get('base', 0.00)
                    line.aliquota_cofins = tax_id.amount

    cfop_id = fields.Many2one('br_account.cfop', string="CFOP")
    icms_cst_normal = fields.Char(string="CST ICMS", size=5)
    icms_csosn_simples = fields.Char(string="CSOSN ICMS", size=5)
    icms_st_aliquota_mva = fields.Float(string=u'Alíquota MVA (%)',
                                        digits=dp.get_precision('Account'))
    aliquota_icms_proprio = fields.Float(
        string=u'Alíquota ICMS Próprio (%)',
        digits=dp.get_precision('Account'))
    icms_aliquota_reducao_base = fields.Float(
        string=u'Redução Base ICMS (%)', digits=dp.get_precision('Account'))
    icms_st_aliquota_reducao_base = fields.Float(
        string=u'Redução Base ICMS ST(%)', digits=dp.get_precision('Account'))
    ipi_cst = fields.Char(string='CST IPI', size=5)
    pis_cst = fields.Char(string='CST PIS', size=5)
    cofins_cst = fields.Char(string='CST COFINS', size=5)
    valor_desconto = fields.Float(
        string='Vlr. Desc. (-)', store=True,
        digits=dp.get_precision('Sale Price'))
    valor_bruto = fields.Float(
        string='Vlr. Bruto', store=True, compute=_compute_amount_line_all,
        digits=dp.get_precision('Sale Price'))
    valor_icms = fields.Float(string='Valor ICMS', store=True,
                              digits=dp.get_precision('Sale Price'),
                              compute=_compute_amount_line_all)
    valor_ipi = fields.Float(string='Valor IPI', store=True,
                             digits=dp.get_precision('Sale Price'),
                             compute=_compute_amount_line_all)
    valor_pis = fields.Float(string='Valor PIS', store=True,
                             digits=dp.get_precision('Sale Price'),
                             compute=_compute_amount_line_all)
    valor_cofins = fields.Float(string='Valor COFINS', store=True,
                                digits=dp.get_precision('Sale Price'),
                                compute=_compute_amount_line_all)
    base_icms = fields.Float(string='Base ICMS', store=True,
                             compute=_compute_amount_line_all)
    base_ipi = fields.Float(string='Base IPI', store=True,
                            compute=_compute_amount_line_all)
    base_pis = fields.Float(string='Base PIS', store=True,
                            compute=_compute_amount_line_all)
    base_cofins = fields.Float(string='Base COFINS', store=True,
                               compute=_compute_amount_line_all)
    aliquota_icms = fields.Float()
    aliquota_ipi = fields.Float()
    aliquota_pis = fields.Float()
    aliquota_cofins = fields.Float()
