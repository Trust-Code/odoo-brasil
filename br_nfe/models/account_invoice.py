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
                item.nfe_exception = (docs[0].state in ('error', 'denied'))
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

    @api.multi
    def action_invoice_draft(self):
        for item in self:
            docs = self.env['invoice.eletronic'].search(
                [('invoice_id', '=', item.id)])
            for doc in docs:
                if doc.state in ('done', 'denied', 'cancel'):
                    raise UserError('Nota fiscal já emitida para esta fatura - \
                                    Duplique a fatura para continuar')
        return super(AccountInvoice, self).action_invoice_draft()

    @api.multi
    def action_number(self):
        super(AccountInvoice, self).action_number()
        sequence = True
        while sequence:
            sequence = self.env['invoice.eletronic.inutilized'].search([
                ('numeration_start', '<=', self.internal_number),
                ('numeration_end', '>=', self.internal_number)], limit=1) or \
                self.env['invoice.eletronic'].search([
                    ('numero', '=', self.internal_number)
                ], order='numero desc', limit=1)
            if sequence:
                self.internal_number += 1
        return True

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
        if inv.commercial_partner_id.is_company:
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
        if inv.commercial_partner_id.is_company:
            if inv.commercial_partner_id.inscr_est:
                ind_ie_dest = '1'
            elif inv.commercial_partner_id.state_id.code in ('AM', 'BA', 'CE',
                                                             'GO', 'MG', 'MS',
                                                             'MT', 'PE', 'RN',
                                                             'SP'):
                ind_ie_dest = '9'
            else:
                ind_ie_dest = '2'
        else:
            ind_ie_dest = '9'
        if inv.commercial_partner_id.indicador_ie_dest:
            ind_ie_dest = inv.commercial_partner_id.indicador_ie_dest
        res['ind_ie_dest'] = ind_ie_dest

        # Duplicatas
        duplicatas = []
        count = 1
        for parcela in inv.receivable_move_line_ids.sorted(lambda x: x.name):
            duplicatas.append((0, None, {
                'numero_duplicata': "%s/%02d" % (inv.internal_number, count),
                'data_vencimento': parcela.date_maturity,
                'valor': parcela.credit or parcela.debit,
            }))
            count += 1
        res['duplicata_ids'] = duplicatas

        # Documentos Relacionados
        documentos = []
        for doc in inv.fiscal_document_related_ids:
            documentos.append((0, None, {
                'invoice_related_id': doc.invoice_related_id.id,
                'document_type': doc.document_type,
                'access_key': doc.access_key,
                'serie': doc.serie,
                'internal_number': doc.internal_number,
                'state_id': doc.state_id.id,
                'cnpj_cpf': doc.cnpj_cpf,
                'cpfcnpj_type': doc.cpfcnpj_type,
                'inscr_est': doc.inscr_est,
                'date': doc.date,
                'fiscal_document_id': doc.fiscal_document_id.id,
            }))

        res['fiscal_document_related_ids'] = documentos
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

        di_importacao = []
        for di in invoice_line.import_declaration_ids:
            adicoes = []
            for di_line in di.line_ids:
                adicoes.append((0, None, {
                    'sequence': di_line.sequence,
                    'name': di_line.name,
                    'manufacturer_code': di_line.manufacturer_code,
                    'amount_discount': di_line.amount_discount,
                    'drawback_number': di_line.drawback_number,
                }))

            di_importacao.append((0, None, {
                'name': di.name,
                'date_registration': di.date_registration,
                'state_id': di.state_id.id,
                'location': di.location,
                'date_release': di.date_release,
                'type_transportation': di.type_transportation,
                'afrmm_value': di.afrmm_value,
                'type_import': di.type_import,
                'thirdparty_cnpj': di.thirdparty_cnpj,
                'thirdparty_state_id': di.thirdparty_state_id.id,
                'exporting_code': di.exporting_code,
                'line_ids': adicoes,
            }))
        vals['import_declaration_ids'] = di_importacao
        vals['informacao_adicional'] = invoice_line.informacao_adicional
        return vals
