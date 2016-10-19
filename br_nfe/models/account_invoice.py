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

    sending_nfe = fields.Boolean(
        string="Enviando NFe?", compute="_compute_nfe_number")
    nfe_exception = fields.Boolean(
        string="Problemas na NFe?", compute="_compute_nfe_number")
    nfe_status = fields.Char(
        string="Mensagem NFe", compute="_compute_nfe_number")
    nfe_number = fields.Integer(
        string="Número NFe", compute="_compute_nfe_number")
    nfe_exception_number = fields.Integer(
        string="Número NFe", compute="_compute_nfe_number")

    def action_preview_danfe(self):
        docs = self.env['invoice.eletronic'].search(
            [('invoice_id', '=', self.id)])
        if not docs:
            raise UserError('Não existe um E-Doc relacionado à esta fatura')
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
        res['ambiente'] = 'homologacao' \
            if inv.company_id.tipo_ambiente == '2' else 'producao'
        if inv.partner_id.is_company:
            res['ind_final'] = '0'
        else:
            res['ind_final'] = '1'
        if inv.fiscal_position_id.ind_final:
            res['ind_final'] = inv.fiscal_position_id.ind_final
        res['ind_pres'] = inv.fiscal_position_id.ind_pres
        res['finalidade_emissao'] = inv.fiscal_position_id.finalidade_emissao
        res['informacoes_legais'] = inv.fiscal_comment
        res['informacoes_complementares'] = inv.comment
        return res

    def _prepare_edoc_item_vals(self, invoice_line):
        vals = super(AccountInvoice, self).\
            _prepare_edoc_item_vals(invoice_line)
        vals['cest'] = invoice_line.product_id.cest or \
            invoice_line.fiscal_classification_id.cest or ''
        vals['has_icms_difal'] = invoice_line.has_icms_difal
        return vals
