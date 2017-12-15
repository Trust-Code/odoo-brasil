# -*- coding: utf-8 -*-
# © 2017 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import models


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    def _return_pdf_invoice(self, doc):
        if self.service_document_id.code == '012':  # Paulistana
            return ''   # TODO Implementar ou não?
        return super(AccountInvoice, self)._return_pdf_invoice(doc)

    def _prepare_edoc_vals(self, inv, inv_lines):
        res = super(AccountInvoice, self)._prepare_edoc_vals(inv, inv_lines)

        res['serie'] = inv.service_serie_id.id
        res['serie_documento'] = inv.service_document_id.code
        res['model'] = inv.service_document_id.code
        return res

    def _prepare_edoc_item_vals(self, line):
        res = super(AccountInvoice, self)._prepare_edoc_item_vals(line)
        return res
