# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models, api
from odoo.exceptions import UserError


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    ambiente_nfse = fields.Selection(
        string="Ambiente NFe", related="company_id.tipo_ambiente_nfse",
        readonly=True)

    def _prepare_edoc_item_vals(self, line):
        res = super(AccountInvoice, self)._prepare_edoc_item_vals(line)
        res['codigo_servico_paulistana'] = \
            line.service_type_id.codigo_servico_paulistana
        return res

    def action_preview_danfse(self):
        docs = self.env['invoice.eletronic'].search(
            [('invoice_id', '=', self.id)])
        if not docs:
            raise UserError(u'Não existe um E-Doc relacionado à esta fatura')
        action = self.env['report'].get_action(
            docs.ids, 'br_nfse.main_template_br_nfse_danfe')
        action['report_type'] = 'qweb-html'
        return action

class AccountInvoiceLine(models.Model):
    _inherit = "account.invoice.line"

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.invoice_id.type == 'out_invoice':
            self.is_cust_invoice = True  
            self.is_supp_invoice = False
        if self.invoice_id.type == 'in_invoice':
            if self.product_id:
                self.is_cust_invoice = False  
                self.is_supp_invoice = True
        return super(AccountInvoiceLine, self)._onchange_product_id()
        
    is_cust_invoice = fields.Boolean(string='Is Customer Invoice', default=False)
    is_supp_invoice = fields.Boolean(string='Is Supplier Invoice', default=False)