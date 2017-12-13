# -*- coding: utf-8 -*-
# © 2012-2015 KMEE (http://www.kmee.com.br)
# @author Luis Felipe Miléo <mileo@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from __future__ import with_statement

import odoo
import base64
import logging
from odoo.exceptions import UserError
from odoo.report.render import render
from odoo.report.interface import report_int
from lxml import etree
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO
_logger = logging.getLogger(__name__)

try:
    from pytrustnfe.nfe import autorizar_nfe
    from pytrustnfe.nfe import retorno_autorizar_nfe
    from pytrustnfe.nfe import recepcao_evento_cancelamento
    from pytrustnfe.certificado import Certificado
    from pytrustnfe.utils import ChaveNFe, gerar_chave, gerar_nfeproc
    from pytrustnfe.nfe.danfe import danfe
except ImportError:
    _logger.info('Cannot import pytrustnfe', exc_info=True)


class external_pdf(render):
    def __init__(self, pdf):
        render.__init__(self)
        self.pdf = pdf
        self.output_type = 'pdf'

    def _render(self):
        return self.pdf


class ReportCustom(report_int):
    """
        Custom report for return boletos
    """

    def create(self, cr, uid, ids, datas, context=False):
        import ipdb
        ipdb.set_trace()

        env = odoo.api.Environment(cr, uid, context or {})

        nfe = env['invoice.eletronic'].search([('id', 'in', context.get(
            'active_ids'))])

        nfe_xml = base64.decodestring(nfe.nfe_processada)
        logo = base64.decodestring(nfe.invoice_id.company_id.logo)
        if logo:
            tmpLogo = StringIO()
            tmpLogo.write(logo)
            tmpLogo.seek(0)
        else:
            tmpLogo = False
        
        xml_element = etree.fromstring(nfe_xml)
        oDanfe = danfe(list_xml=[xml_element], logo=tmpLogo)

        tmpDanfe = StringIO()
        oDanfe.writeto_pdf(tmpDanfe)

        tmpDanfe.reset()
        
        danfe_file = tmpDanfe.getvalue()

        tmpDanfe.close()
        
        self.obj = external_pdf(danfe_file)
        self.obj.render()
        return self.obj.pdf, 'pdf'

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


ReportCustom('report.custom_report_danfe')
