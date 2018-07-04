# -*- coding: utf-8 -*-
# © 2017 Danimar Ribeiro <danimaribeiro@gmail.com>, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models
from odoo.exceptions import UserError


class CancelNFSe(models.TransientModel):
    _name = 'wizard.cancel.nfse'

    edoc_id = fields.Many2one('invoice.eletronic', string="Documento")
    justificativa = fields.Text('Justificativa', size=255, required=True)

    @api.multi
    def action_cancel_nfse(self):
        if self.edoc_id and len(self.justificativa) > 15:
            self.edoc_id.action_cancel_document(
                justificativa=self.justificativa)
        else:
            raise UserError(u"Justificativa deve ter mais de 15 caracteres")
