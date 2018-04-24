# -*- coding: utf-8 -*-
# © 2012-2015 KMEE (http://www.kmee.com.br)
# @author Luis Felipe Miléo <mileo@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from __future__ import with_statement

import pytz
import odoo
import base64
import logging
from odoo.report.render import render
from odoo.report.interface import report_int
from odoo.exceptions import UserError
from lxml import etree
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO
_logger = logging.getLogger(__name__)

try:
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
        Custom report for return nfe
    """

    def create(self, cr, uid, ids, datas, context=False):

        env = odoo.api.Environment(cr, uid, context or {})

        nfes = env['invoice.eletronic'].search([('id', 'in', context.get(
            'active_ids'))])

        xml_element = []
        logo = None
        cce_xml_element = []
        for nfe in nfes:
            if not nfe.nfe_processada:
                raise UserError(u'O seguinte campo não está preenchido: \
                    Xml da NFe - {}'.format(nfe.name))
            nfe_xml = base64.decodestring(nfe.nfe_processada)
            cce_list = env['ir.attachment'].search([
                ('res_model', '=', 'invoice.eletronic'),
                ('res_id', '=', nfe.id),
                ('name', 'like', 'cce-')
            ])

            if cce_list:
                cce_xml = base64.decodestring(cce_list[0].datas)
                cce_xml_element.append(etree.fromstring(cce_xml))

            if nfe.invoice_id.company_id.logo:
                logo = base64.decodestring(nfe.invoice_id.company_id.logo)
            elif nfe.invoice_id.company_id.logo_web:
                logo = base64.decodestring(nfe.invoice_id.company_id.logo_web)

            xml_element.append(etree.fromstring(nfe_xml))

        if logo:
            tmpLogo = StringIO()
            tmpLogo.write(logo)
            tmpLogo.seek(0)
        else:
            tmpLogo = False

        timezone = pytz.timezone(context['tz']) or pytz.utc

        oDanfe = danfe(list_xml=xml_element, logo=tmpLogo,
                       cce_xml=cce_xml_element, timezone=timezone)

        tmpDanfe = StringIO()
        oDanfe.writeto_pdf(tmpDanfe)

        tmpDanfe.reset()

        danfe_file = tmpDanfe.getvalue()

        tmpDanfe.close()

        self.obj = external_pdf(danfe_file)
        self.obj.render()
        return self.obj.pdf, 'pdf'


ReportCustom('report.nfe.custom_report_danfe')
