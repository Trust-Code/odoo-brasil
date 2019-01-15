# -*- coding: utf-8 -*-
# © 2017 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import base64
from odoo import models


class InvoiceEletronic(models.Model):
    _inherit = 'invoice.eletronic'

    def _find_attachment_ids_email(self):
        atts = super(InvoiceEletronic, self)._find_attachment_ids_email()
        attachment_obj = self.env['ir.attachment']
        boleto_report = self.env['ir.actions.report'].search(
            [('report_name', '=',
              'br_boleto.report.print')])
        report_service = boleto_report.xml_id
        boleto, dummy = self.env.ref(report_service).with_context(
            ignore_empty_boleto=True).render_qweb_pdf([self.invoice_id.id])
        if boleto:
            boleto_id = attachment_obj.create(dict(
                name="boleto-%s.pdf" % self.invoice_id.number,
                datas_fname="boleto-%s.pdf" % self.invoice_id.number,
                datas=base64.b64encode(boleto),
                mimetype='application/pdf',
                res_model='account.invoice',
                res_id=self.invoice_id.id,
            ))
            atts.append(boleto_id.id)
        return atts
