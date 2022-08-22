import logging
import base64
from lxml import objectify

from odoo import models, fields
from odoo.exceptions import UserError, RedirectWarning

_logger = logging.getLogger(__file__)


class WizardImportCte(models.TransientModel):
    _name = "wizard.import.cte"
    _description = "Wizard Importacao CTe"

    cte_xml = fields.Binary("XML da CTe")

    def _import_xml(self, xml):
        cte = objectify.fromstring(xml)
        invoice_eletronic = self.env["invoice.eletronic"]
        company_id = self.env.user.company_id
        invoice_eletronic.import_cte(
            company_id,
            cte,
            xml,
            company_id.partner_automation,
            company_id.invoice_automation,
            company_id.tax_automation,
            company_id.supplierinfo_automation,
            False,
            False,
        )

    def action_import_cte(self):
        if not self.cte_xml:
            raise UserError("Por favor, insira um arquivo de CTe.")

        xml = base64.b64decode(self.cte_xml)

        try:
            self._import_xml(xml)
        except (UserError, RedirectWarning) as e:
            msg = "Erro ao importar o xml: CTE\n{}".format(e.name)
            _logger.warning(msg)
            raise UserError(msg)
