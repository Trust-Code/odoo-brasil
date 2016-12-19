# -*- coding: utf-8 -*-
# © 2016 Alessandro Fernandes Martini <alessandrofmartini@gmail.com>, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import base64
import logging
import re
from datetime import datetime
from odoo import api, fields, models
from odoo.exceptions import UserError
_logger = logging.getLogger(__name__)
try:
    from pytrustnfe.nfe import recepcao_evento_carta_correcao
    from pytrustnfe.certificado import Certificado
except ImportError:
    _logger.debug('Cannot import pytrustnfe', exc_info=True)


class WizardCartaCorrecaoEletronica(models.TransientModel):
    _name = 'wizard.carta.correcao.eletronica'

    state = fields.Selection([('drat', 'Provisório'), ('error', 'Erro')],
                             string="Situação")
    correcao = fields.Text(string="Correção", max_length=1000, required=True)
    eletronic_doc_id = fields.Many2one(
        'invoice.eletronic', string="Documento Eletrônico")
    message = fields.Char(string="Mensagem", size=300, readonly=True)
    sent_xml = fields.Binary(string="Xml Envio", readonly=True)
    sent_xml_name = fields.Char(string="Xml Envio", size=30, readonly=True)
    received_xml = fields.Binary(string="Xml Recebimento", readonly=True)
    received_xml_name = fields.Char(
        string="Xml Recebimento", size=30, readonly=True)

    def valida_carta_correcao_eletronica(self):
        if len(self.correcao) < 15:
            raise UserError('Motivo de Correção deve ter mais de ' +
                            '15 caracteres')

    @api.multi
    def send_letter(self):
        self.valida_carta_correcao_eletronica()

        numero_evento = len(self.eletronic_doc_id.cartas_correcao_ids) + 1
        carta = {
            'invoice_id': self.eletronic_doc_id.id,
            'CNPJ': re.sub(
                "[^0-9]", "", self.eletronic_doc_id.company_id.cnpj_cpf or ''),
            'cOrgao':  self.eletronic_doc_id.company_id.state_id.ibge_code,
            'tpAmb': self.eletronic_doc_id.company_id.tipo_ambiente,
            'estado':  self.eletronic_doc_id.company_id.state_id.ibge_code,
            'ambiente': int(self.eletronic_doc_id.company_id.tipo_ambiente),
            'dhEvento': datetime.now().strftime('%Y-%m-%dT%H:%M:%S-00:00'),
            'chNFe': self.eletronic_doc_id.chave_nfe,
            'xCorrecao': self.correcao,
            'tpEvento': '110110',
            'nSeqEvento': numero_evento,
            'idLote': self.id,
            'Id': "ID110110%s%02d" % (self.eletronic_doc_id.chave_nfe,
                                      numero_evento)
        }
        cert = self.eletronic_doc_id.company_id.with_context(
            {'bin_size': False}).nfe_a1_file
        cert_pfx = base64.decodestring(cert)
        certificado = Certificado(
            cert_pfx, self.eletronic_doc_id.company_id.nfe_a1_password)
        resposta = recepcao_evento_carta_correcao(certificado, **carta)

        # TODO Checar a resposta antes de criar a carta
        retorno = resposta['object'].Body.nfeRecepcaoEventoResult.retEnvEvento

        if retorno.cStat == 128 and retorno.retEvento.infEvento.cStat in (135,
                                                                          136):
            eventos = self.env['carta.correcao.eletronica.evento']
            eventos.create({
                'id_cce': carta['Id'],
                'eletronic_doc_id': self.eletronic_doc_id.id,
                'datahora_evento': datetime.now(),
                'tipo_evento': carta['tpEvento'],
                'sequencial_evento': carta['nSeqEvento'],
                'correcao': carta['xCorrecao'],
                'message': retorno.retEvento.infEvento.xEvento,
                'protocolo': retorno.retEvento.infEvento.nProt,
            })
            self.eletronic_doc_id._create_attachment(
                'cce', self.eletronic_doc_id, resposta['sent_xml'])
            self.eletronic_doc_id._create_attachment(
                'cce_ret', self.eletronic_doc_id, resposta['received_xml'])

        else:
            mensagem = "%s - %s" % (retorno.cStat, retorno.xMotivo)
            if retorno.cStat == 128:
                mensagem = "%s - %s" % (retorno.retEvento.infEvento.cStat,
                                        retorno.retEvento.infEvento.xMotivo)
            self.write({
                'state': 'error',
                'message': mensagem,
                'sent_xml': base64.b64encode(resposta['sent_xml']),
                'sent_xml_name': 'cce-envio.xml',
                'received_xml': base64.b64encode(resposta['received_xml']),
                'received_xml_name': 'cce-retorno.xml',
            })

            return {
                "type": "ir.actions.act_window",
                "res_model": "wizard.carta.correcao.eletronica",
                "views": [[False, "form"]],
                "name": "Carta de Correção",
                "target": "new",
                "res_id": self.id,
            }
