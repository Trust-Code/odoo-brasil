# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    def _return_pdf_invoice(self, doc):
        if doc.model == '010':
            return 'br_nfse_imperial.report_br_nfse_danfe_imperial'  # Imperial
        return super(AccountInvoice, self)._return_pdf_invoice(doc)
