# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    def action_preview_danfe(self):
        docs = self.env['invoice.eletronic'].search(
            [('invoice_id', '=', self.id)])
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
        res['informacoes_legais'] = inv.fiscal_comment
        res['informacoes_complementares'] = inv.comment
        return res
