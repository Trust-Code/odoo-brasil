# © 2017 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import base64
import logging
from lxml import etree
from io import BytesIO
from odoo import models

_logger = logging.getLogger(__name__)

try:
    from pytrustnfe.nfe.danfe import danfe
except ImportError:
    _logger.warning('Cannot import pytrustnfe', exc_info=True)


class IrActionsReport(models.Model):
    _inherit = 'ir.actions.report'

    def render_qweb_pdf(self, res_ids, data=None):
        if self.report_name != 'br_nfe.main_template_br_nfe_danfe':
            return super(IrActionsReport, self).render_qweb_pdf(
                res_ids, data=data)

        nfe = self.env['invoice.eletronic'].search([('id', 'in', res_ids)])

        nfe_xml = base64.decodestring(nfe.nfe_processada)

        logo = False
        if nfe.invoice_id.company_id.logo:
            logo = base64.decodestring(nfe.invoice_id.company_id.logo)
        elif nfe.invoice_id.company_id.logo_web:
            logo = base64.decodestring(nfe.invoice_id.company_id.logo_web)

        if logo:
            tmpLogo = BytesIO()
            tmpLogo.write(logo)
            tmpLogo.seek(0)
        else:
            tmpLogo = False

        xml_element = etree.fromstring(nfe_xml)
        oDanfe = danfe(list_xml=[xml_element], logo=tmpLogo)

        tmpDanfe = BytesIO()
        oDanfe.writeto_pdf(tmpDanfe)
        danfe_file = tmpDanfe.getvalue()
        tmpDanfe.close()

        return danfe_file, 'pdf'
