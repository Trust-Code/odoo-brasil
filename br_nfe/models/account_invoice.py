# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models
from odoo.exceptions import UserError


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    def action_preview_danfe(self):
        docs = self.env['invoice.eletronic'].search(
            [('invoice_id', '=', self.id)])
        if not docs:
            raise UserError('Não existe um E-Doc relacionado à esta cobrança')
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
        import ipdb; ipdb.set_trace()
        res['ambiente'] = 'homologacao' \
            if inv.company_id.tipo_ambiente == '2' else 'producao'
        if inv.partner_id.is_company:
            res['ind_final'] = '0'
        else:
            res['ind_final'] = '1'
        if inv.fiscal_position_id.ind_final:
            res['ind_final'] = inv.fiscal_position_id.ind_final
        res['ind_pres'] = inv.fiscal_position_id.ind_pres
        res['informacoes_legais'] = inv.fiscal_comment
        res['informacoes_complementares'] = inv.comment
        return res

    # TODO: REGRA DE ICMS INTERESTADUAL
    def _prepare_edoc_item_vals(self, invoice_line):
        vals = super(AccountInvoice, self).\
            _prepare_edoc_item_vals(invoice_line)
        SUL = [41, 42, 43]
        SUDESTE = [31, 32, 33, 35]
        CENTRO_OESTE = [50, 51, 52, 53]
        NORDESTE = [21, 22, 23, 24, 25, 26, 27, 28, 29]
        NORTE = [11, 12, 13, 14, 15, 16, 17, ]

        if invoice_line.partner_id.state_id.ibge_code in NORDESTE:
            if invoice_line.company_id.state_id.ibge_code in SUL:
                vals['icms_bc_uf_dest']
                vals['icms_aliquota_fcp_uf_dest']
                vals['icms_aliquota_uf_dest']
                vals['icms_aliquota_interestadual']
                vals['icms_aliquota_inter_part']
                vals['icms_fcp_uf_dest']
                vals['icms_uf_dest']
                vals['icms_uf_remet']
