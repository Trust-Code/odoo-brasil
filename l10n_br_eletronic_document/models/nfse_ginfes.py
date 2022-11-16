import re
import pytz
import time
import base64
import logging
from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools.safe_eval import safe_eval

_logger = logging.getLogger(__name__)

try:
    from pytrustnfe.nfse.ginfes import xml_recepcionar_lote_rps
    from pytrustnfe.nfse.ginfes import recepcionar_lote_rps
    from pytrustnfe.nfse.ginfes import consultar_situacao_lote
    from pytrustnfe.nfse.ginfes import consultar_lote_rps
    from pytrustnfe.nfse.ginfes import cancelar_nfse
    from pytrustnfe.certificado import Certificado
except ImportError:
    _logger.error('Cannot import pytrustnfe', exc_info=True)



def send_api(certificate, password, list_rps):
    return {
        'code': 201,
        'entity': {
            'protocolo_nfe': "protocolo",
            # get last 9 digits :)
            'numero_nfe': 123,
        },
        'xml': "",
    }
    cert = self.company_id.with_context(
        {'bin_size': False}).nfe_a1_file
    cert_pfx = base64.decodestring(cert)

    certificado = Certificado(
        cert_pfx, self.company_id.nfe_a1_password)

    consulta_lote = None
    recebe_lote = None

    # Envia o lote apenas se não existir protocolo
    if not self.recibo_nfe:
        xml_to_send = base64.decodestring(self.xml_to_send)
        recebe_lote = recepcionar_lote_rps(
            certificado, xml=xml_to_send, ambiente=self.ambiente)

        retorno = recebe_lote['object']
        if "NumeroLote" in dir(retorno):
            self.recibo_nfe = retorno.Protocolo
            # Espera alguns segundos antes de consultar
            time.sleep(5)
        else:
            mensagem_retorno = retorno.ListaMensagemRetorno\
                .MensagemRetorno
            self.codigo_retorno = mensagem_retorno.Codigo
            self.mensagem_retorno = mensagem_retorno.Mensagem
            self._create_attachment(
                'nfse-ret', self,
                recebe_lote['received_xml'])
            return
    # Monta a consulta de situação do lote
    # 1 - Não Recebido
    # 2 - Não processado
    # 3 - Processado com erro
    # 4 - Processado com sucesso
    obj = {
        'cnpj_prestador': re.sub(
            '[^0-9]', '', self.company_id.cnpj_cpf),
        'inscricao_municipal': re.sub(
            '[^0-9]', '', self.company_id.inscr_mun),
        'protocolo': self.recibo_nfe,
    }
    consulta_situacao = consultar_situacao_lote(
        certificado, consulta=obj, ambiente=self.ambiente)
    ret_rec = consulta_situacao['object']

    if "Situacao" in dir(ret_rec):
        if ret_rec.Situacao in (3, 4):

            consulta_lote = consultar_lote_rps(
                certificado, consulta=obj, ambiente=self.ambiente)
            retLote = consulta_lote['object']

            if "ListaNfse" in dir(retLote):
                self.state = 'done'
                self.codigo_retorno = '100'
                self.mensagem_retorno = 'NFSe emitida com sucesso'
                self.verify_code = retLote.ListaNfse.CompNfse \
                    .Nfse.InfNfse.CodigoVerificacao
                self.numero_nfse = \
                    retLote.ListaNfse.CompNfse.Nfse.InfNfse.Numero
            else:
                mensagem_retorno = retLote.ListaMensagemRetorno \
                    .MensagemRetorno
                self.codigo_retorno = mensagem_retorno.Codigo
                self.mensagem_retorno = mensagem_retorno.Mensagem

        elif ret_rec.Situacao == 1:  # Reenviar caso não recebido
            self.codigo_retorno = ''
            self.mensagem_retorno = 'Aguardando envio'
            self.state = 'draft'
        else:
            self.state = 'waiting'
            self.codigo_retorno = '2'
            self.mensagem_retorno = 'Lote aguardando processamento'
    else:
        self.codigo_retorno = \
            ret_rec.ListaMensagemRetorno.MensagemRetorno.Codigo
        self.mensagem_retorno = \
            ret_rec.ListaMensagemRetorno.MensagemRetorno.Mensagem

    self.env['invoice.eletronic.event'].create({
        'code': self.codigo_retorno,
        'name': self.mensagem_retorno,
        'invoice_eletronic_id': self.id,
    })
    if recebe_lote:
        self._create_attachment(
            'nfse-ret', self,
            recebe_lote['received_xml'])
    if consulta_lote:
        self._create_attachment(
            'rec', self, consulta_lote['sent_xml'])
        self._create_attachment(
            'rec-ret', self,
            consulta_lote['received_xml'])

def cancel_api(certificate, password, vals):
    return {
        'code': 200,
        'message': 'Nota Fiscal Cancelada',
    }
    if self.model not in ('002'):
        return super(InvoiceEletronic, self).action_cancel_document(
            justificativa=justificativa)

    cert = self.company_id.with_context(
        {'bin_size': False}).nfe_a1_file
    cert_pfx = base64.decodestring(cert)

    certificado = Certificado(
        cert_pfx, self.company_id.nfe_a1_password)

    company = self.company_id
    city_prestador = self.company_id.partner_id.city_id
    canc = {
        'cnpj_prestador': re.sub('[^0-9]', '', company.cnpj_cpf),
        'inscricao_municipal': re.sub('[^0-9]', '', company.inscr_mun),
        'cidade': '%s%s' % (city_prestador.state_id.ibge_code,
                            city_prestador.ibge_code),
        'numero_nfse': self.numero_nfse,
        'codigo_cancelamento': '1',
        'senha': self.company_id.senha_ambiente_nfse
    }
    cancel = cancelar_nfse(
        certificado, cancelamento=canc, ambiente=self.ambiente)
    retorno = cancel['object'].Body.CancelarNfseResponse.CancelarNfseResult
    if "Cancelamento" in dir(retorno):
        self.state = 'cancel'
        self.codigo_retorno = '100'
        self.mensagem_retorno = u'Nota Fiscal de Serviço Cancelada'
    else:
        # E79 - Nota já está cancelada
        if retorno.ListaMensagemRetorno.MensagemRetorno.Codigo != 'E79':
            mensagem = "%s - %s" % (
                retorno.ListaMensagemRetorno.MensagemRetorno.Codigo,
                retorno.ListaMensagemRetorno.MensagemRetorno.Mensagem
            )
            raise UserError(mensagem)

        self.state = 'cancel'
        self.codigo_retorno = '100'
        self.mensagem_retorno = u'Nota Fiscal de Serviço Cancelada'

    self.env['invoice.eletronic.event'].create({
        'code': self.codigo_retorno,
        'name': self.mensagem_retorno,
        'invoice_eletronic_id': self.id,
    })
    self._create_attachment('canc', self, cancel['sent_xml'])
    self._create_attachment('canc-ret', self, cancel['received_xml'])
