# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DTFT


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    ambiente_nfse = fields.Selection(
        string="Ambiente NFe", related="company_id.tipo_ambiente_nfse",
        readonly=True)

    def _return_pdf_invoice(self, doc):
        if self.fiscal_document_id.code == '001':  # Paulistana
            return 'br_nfse.main_template_br_nfse_danfe'
        elif self.fiscal_document_id.code == '002':  # Ginfes
            return 'br_nfse.main_template_br_nfse_danfe_ginfes'
        elif self.fiscal_document_id.code == '008':  # Simpliss
            return 'br_nfse.main_template_br_nfse_danfe_simpliss'
        elif self.fiscal_document_id.code == '010':
            return 'br_nfse.main_template_br_nfse_danfe_imperial'  # Imperial
        elif self.fiscal_document_id.code == '009':  # Susesu
            return {
                "type": "ir.actions.act_url",
                "url": doc.url_danfe,
                "target": "_blank",
            }
        return super(AccountInvoice, self)._return_pdf_invoice(doc)

    def _prepare_edoc_vals(self, inv):
        res = super(AccountInvoice, self)._prepare_edoc_vals(inv)

        res['ambiente_nfse'] = 'homologacao' \
            if inv.company_id.tipo_ambiente_nfse == '2' else 'producao'

        if self.invoice_model == '001':
            dt = datetime.strptime(self.date_invoice, '%Y-%m-%d')
            dt_now = datetime.now()
            dt = datetime(dt.year, dt.month, dt.day, dt_now.hour,
                          dt_now.minute, dt_now.second)
            dt = datetime.strftime(dt, DTFT)
            res['data_emissao'] = dt
            res['data_fatura'] = dt

        return res

    def _prepare_edoc_item_vals(self, line):
        res = super(AccountInvoice, self)._prepare_edoc_item_vals(line)
        res['codigo_servico_paulistana'] = \
            line.service_type_id.codigo_servico_paulistana
        res['codigo_tributacao_municipio'] = \
            line.service_type_id.codigo_tributacao_municipio
        return res
