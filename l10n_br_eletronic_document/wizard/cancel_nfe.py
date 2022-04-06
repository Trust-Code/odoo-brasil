from odoo import api, fields, models, _
from odoo.exceptions import UserError


class CancelNFe(models.TransientModel):
    _name = 'wizard.cancel.nfe'
    _description = "Cancelamento NF-e"

    edoc_id = fields.Many2one('eletronic.document', string="Documento")
    justificativa = fields.Text('Justificativa', required=True)
    state = fields.Selection([('drat', 'Provisório'), ('error', u'Erro')],
                             string="Situação")
    message = fields.Char(string="Mensagem", size=300, readonly=True)
    sent_xml = fields.Binary(string="Xml Envio", readonly=True)
    sent_xml_name = fields.Char(string="Nome Xml Envio", size=30, readonly=True)
    received_xml = fields.Binary(string="Xml Recebimento", readonly=True)
    received_xml_name = fields.Char(string="Nome Xml Recebimento", size=30, readonly=True)

    def action_cancel_nfe(self):
        if self.edoc_id and len(self.justificativa) > 15:
            return self.edoc_id.action_cancel_document(
                justificativa=self.justificativa)
        else:
            raise UserError(_("Justificativa deve ter mais de 15 caracteres"))
