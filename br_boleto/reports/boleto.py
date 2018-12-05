# © 2018 Danimar Ribeiro <danimaribeiro@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import models
from ..boleto.document import Boleto


class IrActionsReport(models.Model):
    _inherit = 'ir.actions.report'

    def render_qweb_pdf(self, res_ids, data=None):

        if not self.name == 'boleto-payment-order-line':
            return super(IrActionsReport, self).render_qweb_pdf(
                res_ids, data=data)

        order_line_ids = self.env['payment.order.line'].browse(res_ids)
        boleto_list = order_line_ids.generate_boleto_list()

        pdf_string = Boleto.get_pdfs(boleto_list)
        return pdf_string, 'pdf'
