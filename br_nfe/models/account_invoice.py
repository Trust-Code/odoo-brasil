# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models
from odoo.exceptions import UserError


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def _compute_nfe_number(self):
        for item in self:
            docs = self.env['invoice.eletronic'].search(
                [('invoice_id', '=', item.id)])
            if docs:
                item.nfe_number = docs[0].numero
                item.nfe_exception_number = docs[0].numero
                item.nfe_exception = docs[0].state == 'error'
                item.sending_nfe = docs[0].state == 'draft'
                item.nfe_status = '%s - %s' % (
                    docs[0].codigo_retorno, docs[0].mensagem_retorno)

    ambiente_nfe = fields.Selection(
        string="Ambiente NFe", related="company_id.tipo_ambiente")
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

    def action_preview_danfe(self):
        docs = self.env['invoice.eletronic'].search(
            [('invoice_id', '=', self.id)])
        if not docs:
            raise UserError(u'Não existe um E-Doc relacionado à esta fatura')
        action = self.env['report'].get_action(
            docs.ids, 'br_nfe.main_template_br_nfe_danfe')
        action['report_type'] = 'qweb-html'
        return action

    def invoice_print(self):
        if self.fiscal_document_id.code == '55':
            docs = self.env['invoice.eletronic'].search(
                [('invoice_id', '=', self.id)])
            return self.env['report'].get_action(
                docs.ids, 'br_nfe.main_template_br_nfe_danfe')
        else:
            return super(AccountInvoice, self).invoice_print()

    def _prepare_edoc_vals(self, inv):
        res = super(AccountInvoice, self)._prepare_edoc_vals(inv)

        res['ind_pres'] = inv.fiscal_position_id.ind_pres
        res['finalidade_emissao'] = inv.fiscal_position_id.finalidade_emissao
        res['informacoes_legais'] = inv.fiscal_comment
        res['informacoes_complementares'] = inv.comment
        res['numero_fatura'] = inv.number
        res['fatura_bruto'] = inv.total_bruto
        res['fatura_desconto'] = inv.total_desconto
        res['fatura_liquido'] = inv.amount_total
        res['pedido_compra'] = inv.name
        res['valor_icms_uf_remet'] = inv.valor_icms_uf_remet
        res['valor_icms_uf_dest'] = inv.valor_icms_uf_dest
        res['valor_icms_fcp_uf_dest'] = inv.valor_icms_fcp_uf_dest

        res['ambiente'] = 'homologacao' \
            if inv.company_id.tipo_ambiente == '2' else 'producao'

        # Indicador Consumidor Final
        if inv.partner_id.is_company:
            res['ind_final'] = '0'
        else:
            res['ind_final'] = '1'
        res['ind_dest'] = '1'
        if inv.company_id.state_id != inv.commercial_partner_id.state_id:
            res['ind_dest'] = '2'
        if inv.company_id.country_id != inv.commercial_partner_id.country_id:
            res['ind_dest'] = '3'
        if inv.fiscal_position_id.ind_final:
            res['ind_final'] = inv.fiscal_position_id.ind_final

        # Indicador IE Destinatário
        ind_ie_dest = False
        if inv.partner_id.is_company:
            if inv.partner_id.inscr_est:
                ind_ie_dest = '1'
            elif inv.partner_id.state_id.code in ('AM', 'BA', 'CE', 'GO',
                                                  'MG', 'MS', 'MT', 'PE',
                                                  'RN', 'SP'):
                ind_ie_dest = '9'
            else:
                ind_ie_dest = '2'
        else:
            ind_ie_dest = '9'
        if inv.partner_id.indicador_ie_dest:
            ind_ie_dest = inv.partner_id.indicador_ie_dest
        res['ind_ie_dest'] = ind_ie_dest

        # Duplicatas
        duplicatas = []
        for parcela in inv.receivable_move_line_ids:
            duplicatas.append((0, None, {
                'numero_duplicata': parcela.name,
                'data_vencimento': parcela.date_maturity,
                'valor': parcela.credit or parcela.debit,
            }))
        res['duplicata_ids'] = duplicatas

        return res

    def _prepare_edoc_item_vals(self, invoice_line):
        vals = super(AccountInvoice, self).\
            _prepare_edoc_item_vals(invoice_line)
        vals['cest'] = invoice_line.product_id.cest or \
            invoice_line.fiscal_classification_id.cest or ''
        vals['classe_enquadramento_ipi'] = \
            invoice_line.fiscal_classification_id.classe_enquadramento or ''
        vals['codigo_enquadramento_ipi'] = \
            invoice_line.fiscal_classification_id.codigo_enquadramento or '999'
        vals['tem_difal'] = invoice_line.tem_difal
        vals['icms_bc_uf_dest'] = invoice_line.icms_bc_uf_dest
        vals['icms_aliquota_interestadual'] = \
            invoice_line.tax_icms_inter_id.amount or 0.0
        vals['icms_aliquota_uf_dest'] = \
            invoice_line.tax_icms_intra_id.amount or 0.0
        vals['icms_aliquota_fcp_uf_dest'] = \
            invoice_line.tax_icms_fcp_id.amount or 0.0
        vals['icms_uf_remet'] = invoice_line.icms_uf_remet or 0.0
        vals['icms_uf_dest'] = invoice_line.icms_uf_dest or 0.0
        vals['icms_fcp_uf_dest'] = invoice_line.icms_fcp_uf_dest or 0.0
        vals['informacao_adicional'] = invoice_line.informacao_adicional
        return vals
