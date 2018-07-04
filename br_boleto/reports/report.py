# -*- coding: utf-8 -*-
# © 2012-2015 KMEE (http://www.kmee.com.br)
# @author Luis Felipe Miléo <mileo@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import models
from odoo.exceptions import UserError
from ..boleto.document import Boleto


class IrActionsReport(models.Model):
    _inherit = 'ir.actions.report'

    # report_type = fields.Selection(selection_add=[('raw-pdf', 'PDF')])

    def render_qweb_pdf(self, res_ids, data=None):

        if not self.name == 'Boleto':
            return super(IrActionsReport, self).render_qweb_pdf(
                res_ids, data=data)

        active_ids = res_ids
        # active_model = self.env.context.get('origin_model')

        ids_move_lines = []
        aml_obj = self.env['account.move.line']
        if self.model == 'account.invoice':
            ai_obj = self.env['account.invoice']
            for account_invoice in ai_obj.browse(active_ids):
                for move_line in account_invoice.receivable_move_line_ids:
                    ids_move_lines.append(move_line.id)
        elif self.model == 'account.move.line':
            ids_move_lines = active_ids
        else:
            raise UserError(u'Parâmetros inválidos')
        boleto_list = aml_obj.browse(ids_move_lines).action_register_boleto()
        if not boleto_list:
            raise UserError(
                u"""Error
Não é possível gerar os boletos
Certifique-se que a fatura esteja confirmada e o
forma de pagamento seja duplicatas""")
        pdf_string = Boleto.get_pdfs(boleto_list)
        return pdf_string, 'pdf'
