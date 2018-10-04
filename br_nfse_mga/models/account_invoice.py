# © 2018 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import models, fields


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    def _return_pdf_invoice(self, doc):
        if doc.model == '015':  # Maringá,PR
            return 'br_nfse_mga.report_br_nfse_danfe_mga'
        return super(AccountInvoice, self)._return_pdf_invoice(doc)

    def _prepare_edoc_item_vals(self, line):
        res = super(AccountInvoice, self)._prepare_edoc_item_vals(line)
        res['codigo_tributacao_municipio'] = \
            line.service_type_id.codigo_tributacao_municipio
        res['exigibilidade_iss'] = line.exigibilidade_iss
        return res


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    exigibilidade_iss = fields.Selection(
        string="Exigibilidade ISS",
        selection=[
            ('1', 'Exigível'),
            ('2', 'Não incidência'),
            ('3', 'Isenção'),
            ('4', 'Exportação'),
            ('5', 'Imunidade'),
            ('6', 'Exigibilidade Suspensa por Decisão Judicial'),
            ('7', 'Exigibilidade Suspensa por Processo Administrativo '),
        ],
    )
