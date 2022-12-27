# © 2018 Danimar Ribeiro <danimaribeiro@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import models
from ..boleto.document import Boleto, BoletoItau


class IrActionsReport(models.Model):
    _inherit = "ir.actions.report"

    def _render_qweb_html(self, res_ids, data=None):
        xml_id = list(self.get_xml_id().values())
        if (
            xml_id
            and xml_id[0] != "l10n_br_banco_itau.action_report_boleto_itau"
        ):
            return super(IrActionsReport, self)._render_qweb_html(
                res_ids, data=data
            )

    def _render_qweb_pdf(self, res_ids, data=None):
        xml_id = list(self.get_xml_id().values())
        if (
            xml_id
            and xml_id[0] == "l10n_br_banco_itau.action_report_boleto_itau"
        ):
            payment_ids = self.env["payment.transaction"].search(
                [("id", "in", res_ids), ("state", "in", ["pending", "draft"])]
            )
            boleto_list = []
            for pay in payment_ids:
                boleto_list.append(BoletoItau(pay, pay.l10n_br_itau_nosso_numero))
            pdf_string = Boleto.get_pdfs(boleto_list)
            return pdf_string, "pdf"
        return super(IrActionsReport, self)._render_qweb_pdf(
            res_ids, data=data
        )
