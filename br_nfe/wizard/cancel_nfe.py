# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro <danimaribeiro@gmail.com>, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models
from odoo.exceptions import UserError


class CancelNFe(models.TransientModel):
    _name = 'wizard.cancel.nfe'

    edoc_id = fields.Many2one('invoice.eletronic', string="Documento")
    justificativa = fields.Text('Justificativa', size=255, required=True)
    state = fields.Selection([('drat', u'Provisório'), ('error', u'Erro')],
                             string="Situação")
    message = fields.Char(string=u"Mensagem", size=300, readonly=True)
    sent_xml = fields.Binary(string="Xml Envio", readonly=True)
    sent_xml_name = fields.Char(string=u"Xml Envio", size=30, readonly=True)
    received_xml = fields.Binary(string=u"Xml Recebimento", readonly=True)
    received_xml_name = fields.Char(
        string=u"Xml Recebimento", size=30, readonly=True)

    @api.multi
    def action_cancel_nfe(self):
        if self.edoc_id and len(self.justificativa) > 15:
            return self.edoc_id.action_cancel_document(
                justificativa=self.justificativa)
        else:
            raise UserError(u"Justificativa deve ter mais de 15 caracteres")
