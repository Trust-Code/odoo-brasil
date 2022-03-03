from odoo import models


class EletronicDocument(models.Model):
    _inherit = 'eletronic.document'

    def _find_attachment_ids_email(self):
        atts = super(EletronicDocument, self)._find_attachment_ids_email()
        atts += self.move_id.transaction_ids.filtered(lambda x: x.state in ("draft", "pending")).action_get_pdf_inter()
        return atts
