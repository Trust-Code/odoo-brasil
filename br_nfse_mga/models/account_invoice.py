# © 2018 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import models


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    def _return_pdf_invoice(self, doc):
        if doc.model == '015':  # Maringá,PR
            return 'br_nfse_mga.report_br_nfse_danfe_mga'
        return super(AccountInvoice, self)._return_pdf_invoice(doc)

    def _prepare_edoc_vals(self, invoice, inv_lines, serie_id):
        res = super(AccountInvoice, self)._prepare_edoc_vals(
            invoice, inv_lines, serie_id)
        res['exigibilidade_iss'] = self.fiscal_position_id.exigibilidade_iss
        return res

    def _prepare_edoc_item_vals(self, line):
        res = super(AccountInvoice, self)._prepare_edoc_item_vals(line)
        res['codigo_tributacao_municipio'] = \
            line.service_type_id.codigo_tributacao_municipio
        return res
