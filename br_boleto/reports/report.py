# -*- coding: utf-8 -*-
# © 2012-2015 KMEE (http://www.kmee.com.br)
# @author Luis Felipe Miléo <mileo@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from __future__ import with_statement

import odoo
from odoo.exceptions import UserError
# from odoo.report.render import render
# from odoo.report.interface import report_int
from ..boleto.document import Boleto


# class external_pdf(render):
#     def __init__(self, pdf):
#         render.__init__(self)
#         self.pdf = pdf
#         self.output_type = 'pdf'
# 
#     def _render(self):
#         return self.pdf
#
#
# class ReportCustom(report_int):
#     """
#         Custom report for return boletos
#     """
#
#     def create(self, cr, uid, ids, datas, context=False):
#         env = odoo.api.Environment(cr, uid, context or {})
#
#         active_ids = context.get('active_ids')
#         active_model = context.get('origin_model')
#
#         ids_move_lines = []
#         aml_obj = env['account.move.line']
#         if active_model == 'account.invoice':
#             ai_obj = env['account.invoice']
#             for account_invoice in ai_obj.browse(active_ids):
#                 for move_line in account_invoice.receivable_move_line_ids:
#                     ids_move_lines.append(move_line.id)
#         elif active_model == 'account.move.line':
#             ids_move_lines = active_ids
#         else:
#             raise UserError(u'Parâmetros inválidos')
#         boleto_list = aml_obj.browse(ids_move_lines).action_register_boleto()
#         if not boleto_list:
#             raise UserError(
#                 u"""Error
# Não é possível gerar os boletos
# Certifique-se que a fatura esteja confirmada e o
# forma de pagamento seja duplicatas""")
#         pdf_string = Boleto.get_pdfs(boleto_list)
#         self.obj = external_pdf(pdf_string)
#         self.obj.render()
#         return self.obj.pdf, 'pdf'
#
#
# ReportCustom('report.br_boleto.report.print')
