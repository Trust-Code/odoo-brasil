# -*- coding: utf-8 -*-
# © 2016 Alessandro Fernandes Martini <alessandrofmartini@gmail.com>, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import re
import pytz
import base64
import logging

from datetime import datetime
from odoo import api, fields, models
from odoo.exceptions import UserError
_logger = logging.getLogger(__name__)
try:
    from pytrustnfe.nfe import recepcao_evento_carta_correcao
    from pytrustnfe.certificado import Certificado
except ImportError:
    _logger.debug('Cannot import pytrustnfe', exc_info=True)

COND_USO = "A Carta de Correcao e disciplinada pelo paragrafo 1o-A do art. 7o \
do Convenio S/N, de 15 de dezembro de 1970 e pode ser utilizada para \
regularizacao de erro ocorrido na emissao de documento fiscal, desde que o \
erro nao esteja relacionado com: I - as variaveis que determinam o valor do \
imposto tais como: base de calculo, aliquota, diferenca de preco, quantidade, \
valor da operacao ou da prestacao; II - a correcao de dados cadastrais que \
implique mudanca do remetente ou do destinatario; III - a data de \
emissao ou de saida."


class WizardCartaCorrecaoEletronica(models.TransientModel):
    _name = 'wizard.carta.correcao.eletronica'

    @api.depends('eletronic_doc_id')
    def _default_sequence_number(self):
        return len(self.eletronic_doc_id.cartas_correcao_ids) + 1

    state = fields.Selection([('drat', u'Provisório'), ('error', u'Erro')],
                             string=u"Situação")
    correcao = fields.Text(string=u"Correção", max_length=1000, required=True)
    sequential = fields.Integer(
        string="Sequência Evento", default=_default_sequence_number)
    eletronic_doc_id = fields.Many2one(
        'invoice.eletronic', string=u"Documento Eletrônico")
    message = fields.Char(string=u"Mensagem", size=300, readonly=True)
    sent_xml = fields.Binary(string=u"Xml Envio", readonly=True)
    sent_xml_name = fields.Char(string=u"Xml Envio", size=30, readonly=True)
    received_xml = fields.Binary(string=u"Xml Recebimento", readonly=True)
    received_xml_name = fields.Char(
        string=u"Xml Recebimento", size=30, readonly=True)

    def valida_carta_correcao_eletronica(self):
        if len(self.correcao) < 15:
            raise UserError(u'Motivo de Correção deve ter mais de ' +
                            '15 caracteres')
        if len(self.correcao) > 1000:
            raise UserError(u'Motivo de Correção deve ter menos de ' +
                            '1000 caracteres')

    @api.multi
    def send_letter(self):
        self.valida_carta_correcao_eletronica()

        tz = pytz.timezone(self.env.user.partner_id.tz) or pytz.utc
        dt_evento = datetime.utcnow()
        dt_evento = pytz.utc.localize(dt_evento).astimezone(tz)

        carta = {
            'idLote': self.id,
            'estado':  self.eletronic_doc_id.company_id.state_id.ibge_code,
            'ambiente': int(self.eletronic_doc_id.company_id.tipo_ambiente),
            'modelo': self.eletronic_doc_id.model,
            'eventos': [{
                'invoice_id': self.eletronic_doc_id.id,
                'CNPJ': re.sub(
                    "[^0-9]", "", self.eletronic_doc_id.company_id.cnpj_cpf),
                'cOrgao':  self.eletronic_doc_id.company_id.state_id.ibge_code,
                'tpAmb': self.eletronic_doc_id.company_id.tipo_ambiente,
                'dhEvento':  dt_evento.strftime('%Y-%m-%dT%H:%M:%S-03:00'),
                'chNFe': self.eletronic_doc_id.chave_nfe,
                'xCorrecao': self.correcao,
                'tpEvento': '110110',
                'descEvento': 'Carta de Correcao',
                'xCondUso': COND_USO,
                'nSeqEvento': self.sequential,
                'Id': "ID110110%s%02d" % (
                    self.eletronic_doc_id.chave_nfe, self.sequential),
            }],
        }
        cert = self.eletronic_doc_id.company_id.with_context(
            {'bin_size': False}).nfe_a1_file
        cert_pfx = base64.decodestring(cert)
        certificado = Certificado(
            cert_pfx, self.eletronic_doc_id.company_id.nfe_a1_password)
        resposta = recepcao_evento_carta_correcao(certificado, **carta)

        retorno = resposta['object'].getchildren()[0]
        if retorno.cStat == 128 and retorno.retEvento.infEvento.cStat in (135,
                                                                          136):
            eventos = self.env['carta.correcao.eletronica.evento']
            eventos.create({
                'id_cce': carta['eventos'][0]['Id'],
                'eletronic_doc_id': self.eletronic_doc_id.id,
                'datahora_evento': datetime.now(),
                'tipo_evento': carta['eventos'][0]['tpEvento'],
                'sequencial_evento': carta['eventos'][0]['nSeqEvento'],
                'correcao': carta['eventos'][0]['xCorrecao'],
                'message': retorno.retEvento.infEvento.xMotivo,
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
                'sent_xml': base64.b64encode(
                    resposta['sent_xml'].encode('utf-8')),
                'sent_xml_name': 'cce-envio.xml',
                'received_xml': base64.b64encode(
                    resposta['received_xml'].encode('utf-8')),
                'received_xml_name': 'cce-retorno.xml',
            })

            return {
                "type": "ir.actions.act_window",
                "res_model": "wizard.carta.correcao.eletronica",
                "views": [[False, "form"]],
                "name": u"Carta de Correção",
                "target": "new",
                "res_id": self.id,
            }
