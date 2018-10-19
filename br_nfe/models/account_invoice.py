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

    def invoice_print(self):
        doc = self.env['invoice.eletronic'].search(
            [('invoice_id', '=', self.id)], limit=1)
        if doc.model == '55':
            return self.env.ref(
                'br_nfe.report_br_nfe_danfe').report_action(doc)
        else:
            return super(AccountInvoice, self).invoice_print()

    def _return_pdf_invoice(self, doc):
        if doc.model == '55':
            return 'br_nfe.report_br_nfe_danfe'
        return super(AccountInvoice, self)._return_pdf_invoice(doc)

    def action_number(self, serie_id):

        if not serie_id:
            return

        inv_inutilized = self.env['invoice.eletronic.inutilized'].search([
            ('serie', '=', serie_id.id)], order='numeration_end desc', limit=1)

        if not inv_inutilized:
            return serie_id.internal_sequence_id.next_by_id()

        if inv_inutilized.numeration_end >= \
                serie_id.internal_sequence_id.number_next_actual:
            serie_id.internal_sequence_id.sudo().write(
                {'number_next_actual': inv_inutilized.numeration_end + 1})
        return serie_id.internal_sequence_id.next_by_id()

    def _prepare_edoc_vals(self, inv, inv_lines, serie_id):
        res = super(AccountInvoice, self)._prepare_edoc_vals(
            inv, inv_lines, serie_id)

        # Feito para evitar que o número seja incrementado duas vezes
        if 'numero' not in res:
            numero_nfe = self.action_number(serie_id)
        else:
            numero_nfe = res['numero']

        res['payment_mode_id'] = inv.payment_mode_id.id
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
        res['serie'] = serie_id.id
        res['serie_documento'] = serie_id.code
        res['model'] = serie_id.fiscal_document_id.code
        res['numero_nfe'] = numero_nfe
        res['numero'] = numero_nfe
        res['name'] = 'Documento Eletrônico: nº %s' % numero_nfe
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
                'numero_duplicata': "%03d" % count,
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

        # NFC-e
        res['valor_troco'] = 0.0
        res['metodo_pagamento'] = inv.payment_mode_id.tipo_pagamento or '01'
        res['valor_pago'] = inv.amount_total
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
        vals['icms_aliquota_inter_part'] = \
            invoice_line.icms_aliquota_inter_part or 0.0

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
