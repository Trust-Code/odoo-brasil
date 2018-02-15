# -*- coding: utf-8 -*-
# © 2017 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import models


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    def _return_pdf_invoice(self, doc):
        if self.service_document_id.code == '012':  # Floripa
            return ''   # TODO Implementar ou não?
        return super(AccountInvoice, self)._return_pdf_invoice(doc)
