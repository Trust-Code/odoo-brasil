import re
import base64
from pytrustnfe.nfse.bh import gerar_nfse
from pytrustnfe.nfse.bh import cancelar_nfse

from pytrustnfe.certificado import Certificado
from odoo.exceptions import UserError

import re

def _convert_values(vals):
    # Numero lote
    vals['numero_lote'] =  vals['numero_rps']

    # IdentificacaoRps ~ Status
    vals['numero'] = vals['numero_rps']
    vals['tipo_rps'] = '1'
    vals['natureza_operacao'] = '1'

    if vals['regime_tributario'] == 'simples':
        vals['regime_tributacao'] = '6'
        vals['base_calculo'] = 0
        vals['aliquota_issqn'] = 0
    else:
        vals['regime_tributacao'] = ''
        vals['valor_issqn'] = abs(vals['valor_iss'])

    vals['optante_simples'] = '1' if vals['regime_tributario'] == 'simples' else '2'
    vals['incentivador_cultural'] = '2'
    vals['status'] = '1'

    # Rps Substituído - não está sendo usado no momento

    # Valores
    vals['valor_deducao'] = 0.00
    if vals['valor_iss'] < 0:
        vals['iss_retido'] = '1'
        vals['valor_iss_retido'] = vals['iss_valor_retencao'] = abs(vals['valor_iss'])
        vals['valor_iss'] = 0
    else:
        vals['iss_retido'] = '2'
    vals['aliquota_issqn'] = "%.4f" % abs(vals['itens_servico'][0]['aliquota'])
    vals['descricao'] = vals['discriminacao']

    # Código Serviço
    cod_servico = vals['itens_servico'][0]['codigo_servico']
    for item_servico in vals['itens_servico']:
        if item_servico['codigo_servico'] != cod_servico:
            raise UserError('Não é possível gerar notas de serviço com linhas que possuem código de serviço diferentes.'
                            + '\nPor favor, verifique se todas as linhas de serviço possuem o mesmo código de serviço.'
                            + '\nNome: %s: Código de serviço: %s\nNome: %s: Código de serviço: %s'
                            % (vals['itens_servico'][0]['name'], cod_servico,
                             item_servico['name'], item_servico['codigo_servico']))
    vals['codigo_servico'] = cod_servico
    vals['codigo_tributacao_municipio'] = vals['itens_servico'][0]['codigo_servico_municipio']

    # Prestador
    vals['prestador'] = {}
    vals['prestador']['cnpj'] = re.sub('[^0-9]', '', vals['emissor']['cnpj'])
    vals['prestador']['inscricao_municipal'] = re.sub('\W+','', vals['emissor']['inscricao_municipal'])
    vals['codigo_municipio'] = vals['emissor']['codigo_municipio']

    # Tomador
    vals['tomador'].update(
        vals['tomador']['endereco']
    )
    vals['tomador']['cidade'] =vals['tomador']['codigo_municipio']

    # ValorServicos - ValorPIS - ValorCOFINS - ValorINSS - ValorIR - ValorCSLL - OutrasRetençoes
    # - ValorISSRetido - DescontoIncondicionado - DescontoCondicionado)
    vals['valor_liquido_nfse'] = vals['valor_servico'] \
                                 - (vals.get('valor_pis') or 0) \
                                 - (vals.get('valor_cofins') or 0) \
                                 - (vals.get('valor_inss') or 0) \
                                 - (vals.get('valor_ir') or 0) \
                                 - (vals.get('valor_csll') or 0) \
                                 - (vals.get('outras_retencoes') or 0) \
                                 - (vals.get('valor_iss_retido') or 0)

    # Intermediario e ConstrucaoCivil - não está sendo usado no momento

    return vals


def send_api(certificate, password, list_rps):
    cert_pfx = base64.decodestring(certificate)
    certificado = Certificado(cert_pfx, password)

    vals = list_rps[0]
    vals = _convert_values(vals)

    recebe_lote = gerar_nfse(
        certificado, rps=vals, ambiente=vals['ambiente'],
        client_id=vals['client_id'],
        secret_id=vals['client_secret'],
        username=vals['emissor']['inscricao_municipal'],
        password=vals['user_password'])

    retorno = recebe_lote['object']
    if "ListaNfse" in dir(retorno):
        inf_nfse = retorno.ListaNfse.CompNfse.Nfse.InfNfse
        return {
            'code': 201,
            'entity': {
                'protocolo_nfe': inf_nfse.CodigoVerificacao,
                # get last 9 digits :)
                'numero_nfe': inf_nfse.Numero % 1000000000,
            },
            'xml': recebe_lote['received_xml'].encode('utf-8'),
        }
    else:
        if "ListaMensagemRetornoLote" in dir(retorno):
            mensagem_retorno = retorno.ListaMensagemRetornoLote.MensagemRetorno
        else:
            mensagem_retorno = retorno.ListaMensagemRetorno.MensagemRetorno
        return {
            'code': 400,
            'api_code': mensagem_retorno.Codigo,
            'message': mensagem_retorno.Mensagem,
        }

def cancel_api(certificate, password, vals):
    cert_pfx = base64.decodestring(certificate)
    certificado = Certificado(cert_pfx, password)
    canc = {
        'numero_nfse': vals['numero'],
        'cnpj_prestador': vals['cnpj_cpf'],
        'inscricao_municipal': vals['inscricao_municipal'],
        'cidade': vals['codigo_municipio'],
    }
    resposta = cancelar_nfse(
        certificado, cancelamento=canc,
        ambiente=vals['ambiente'],
        client_id=vals['client_id'],
        secret_id=vals['client_secret'],
        username=vals['inscricao_municipal'],
        password=vals['user_password']
    )
    retorno = resposta['object']
    if "RetCancelamento" in dir(retorno):
        return {
            'code': 200,
            'message': 'Nota Fiscal Cancelada',
            'xml': resposta['received_xml'].split("<?xml version='1.0' encoding='UTF-8'?>")[1].encode('utf - 8')
        }
    else:
        erro_retorno = retorno.ListaMensagemRetorno.MensagemRetorno
        return {
            'code': 400,
            'api_code': erro_retorno.Codigo,
            'message': erro_retorno.Mensagem,
        }
