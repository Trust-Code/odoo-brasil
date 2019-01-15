from openerp import api, models
from odoo.exceptions import UserError


class PaymentCnabReport(models.AbstractModel):
    _name = 'report.br_payment_invoice.report_cnab_payment_invoice'

    @api.model
    def get_report_values(self, docids, data=None):
        report = self.env['ir.actions.report']._get_report_from_name(
            'br_payment_invoice.report_cnab_payment_invoice')
        lines = []
        docs = []
        for docid in docids:
            doc = self.env['account.invoice'].browse(docid)
            docs.append(doc)
            lines.append(doc.get_order_line())
        docargs = {
            'doc_ids': docids,
            'doc_model': report.model,
            'docs': self,
            'lines': lines,
        }
        if not lines:
            raise UserError(
                "Este documento ainda não possui um comprovante de pagamento.")
        return docargs
