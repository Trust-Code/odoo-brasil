import re
import pytz
import time
import base64
import logging
from odoo.exceptions import UserError


_logger = logging.getLogger(__name__)

try:
    from pytrustnfe.nfse.ginfes import recepcionar_lote_rps
    from pytrustnfe.nfse.ginfes import consultar_lote_rps
    from pytrustnfe.nfse.ginfes import cancelar_nfse
    from pytrustnfe.certificado import Certificado
except ImportError:
    _logger.error('Cannot import pytrustnfe', exc_info=True)


def _convert_values(vals):
    result = {'lista_rps': vals}

    result['numero_lote'] =  vals[0]['numero_rps']
    result['cnpj_prestador'] = vals[0]['emissor']['cnpj']
    result['inscricao_municipal'] = vals[0]["emissor"]['inscricao_municipal']

    for rps in vals:

        rps['numero'] = rps['numero_rps']
        rps['tipo_rps'] = '1'
        rps['natureza_operacao'] = '1'
        rps['data_emissao'] = rps['data_emissao_hora']

        # Prestador
        rps['prestador'] = {}
        rps['prestador']['cnpj'] = re.sub('[^0-9]', '', rps['emissor']['cnpj'])
        rps['prestador']['inscricao_municipal'] = re.sub('\W+','', rps['emissor']['inscricao_municipal'])
        rps['codigo_municipio'] = rps['emissor']['codigo_municipio']
        rps['cnae_servico'] = rps['emissor']['cnae']

        rps['optante_simples'] = '1' if rps['regime_tributario'] == 'simples' else '2'
        rps['incentivador_cultural'] = '2'
        rps['status'] = '1'

        # Tomador
        rps['tomador'].update(
            rps['tomador']['endereco']
        )
        rps['tomador']['cidade'] = rps['tomador']['codigo_municipio']

        if rps['regime_tributario'] == 'simples':
            rps['regime_tributacao'] = '6'
            rps['base_calculo'] = ''
            rps['aliquota_issqn'] = ''
        else:
            rps['regime_tributacao'] = ''
            rps['valor_issqn'] = abs(rps['valor_iss'])

        # Valores
        rps['valor_deducao'] = 0.00
        if rps['valor_iss'] < 0:
            rps['iss_retido'] = '1'
            rps['valor_iss_retido'] = rps['iss_valor_retencao'] = abs(rps['valor_iss'])
            rps['valor_iss'] = 0
        else:
            rps['iss_retido'] = '2'
        rps['aliquota_issqn'] = "%.4f" % abs(rps['itens_servico'][0]['aliquota'])
        rps['descricao'] = rps['discriminacao']

        # Código Serviço
        cod_servico = rps['itens_servico'][0]['codigo_servico']
        for item_servico in rps['itens_servico']:
            if item_servico['codigo_servico'] != cod_servico:
                raise UserError('Não é possível gerar notas de serviço com linhas que possuem código de serviço diferentes.'
                                + '\nPor favor, verifique se todas as linhas de serviço possuem o mesmo código de serviço.'
                                + '\nNome: %s: Código de serviço: %s\nNome: %s: Código de serviço: %s'
                                % (rps['itens_servico'][0]['name'], cod_servico,
                                item_servico['name'], item_servico['codigo_servico']))
        rps['codigo_servico'] = cod_servico
        rps['codigo_tributacao_municipio'] = rps['itens_servico'][0]['codigo_servico_municipio']

        # ValorServicos - ValorPIS - ValorCOFINS - ValorINSS - ValorIR - ValorCSLL - OutrasRetençoes
        # - ValorISSRetido - DescontoIncondicionado - DescontoCondicionado)
        rps['valor_liquido_nfse'] = rps['valor_servico'] \
                                    - (rps.get('valor_pis') or 0) \
                                    - (rps.get('valor_cofins') or 0) \
                                    - (rps.get('valor_inss') or 0) \
                                    - (rps.get('valor_ir') or 0) \
                                    - (rps.get('valor_csll') or 0) \
                                    - (rps.get('outras_retencoes') or 0) \
                                    - (rps.get('valor_iss_retido') or 0)

    return result


def send_api(certificate, password, edocs):
    cert_pfx = base64.decodestring(certificate)
    certificado = Certificado(cert_pfx, password.encode("utf-8"))

    nfse_values = _convert_values(edocs)

    recebe_lote = recepcionar_lote_rps(
        certificado, nfse=nfse_values, ambiente=edocs[0]['ambiente'])

    retorno = recebe_lote['object']
    if "NumeroLote" in dir(retorno):
        recibo_nfe = retorno.Protocolo
        # Espera alguns segundos antes de consultar
        time.sleep(4)
    else:
        erro_retorno = retorno.ListaMensagemRetorno.MensagemRetorno
        return {
            'code': 400,
            'api_code': erro_retorno.Codigo,
            'message': erro_retorno.Mensagem,
        }

    obj = {
        'cnpj_prestador': re.sub('[^0-9]', '', edocs[0]['emissor']['cnpj']),
        'inscricao_municipal': re.sub('[^0-9]', '', edocs[0]['emissor']['inscricao_municipal']),
        'protocolo': recibo_nfe,
    }
    while True:
        consulta_lote = consultar_lote_rps(
            certificado, consulta=obj, ambiente=edocs[0]['ambiente'])
        retLote = consulta_lote['object']

        if "ListaNfse" in dir(retLote):
            return {
                'code': 201,
                'entity': {
                    'protocolo_nfe': retLote.ListaNfse.CompNfse.Nfse.InfNfse.CodigoVerificacao,
                    'numero_nfe': retLote.ListaNfse.CompNfse.Nfse.InfNfse.Numero,
                },
                'xml': recebe_lote['sent_xml'].encode('utf-8'),
            }
        else:
            erro_retorno = retLote.ListaMensagemRetorno.MensagemRetorno
            if erro_retorno.Codigo in ("E4", "A02"):
                time.sleep(5)
                continue
            return {
                'code': 400,
                'api_code': erro_retorno.Codigo,
                'message': erro_retorno.Mensagem,
            }


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
