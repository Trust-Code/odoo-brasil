import re
import base64
from pytrustnfe.nfse.bh import gerar_nfse
from pytrustnfe.nfse.bh import cancelar_nfse

from pytrustnfe.certificado import Certificado


def _convert_values(vals):
    # Numero lote
    vals['numero_lote'] =  vals['numero_rps']

    # IdentificacaoRps ~ Status
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

    # Prestador
    vals['prestador'] = vals['emissor']

    # Tomador
    vals['tomador'].update(
        vals['tomador']['endereco']
    )

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
    import ipdb
    ipdb.set_trace()
    if "codigoVerificacao" in dir(retorno):
        return {
            'code': 201,
            'entity': {
                'protocolo_nfe': retorno.codigoVerificacao,
                'numero_nfe': retorno.numeroSerie,
            },
            'xml': recebe_lote['received_xml'],
        }
    else:
        return {
            'code': 400,
            'api_code': recebe_lote['status_code'],
            'message': retorno.message,
        }


def cancel_api(certificate, password, vals):
    cert_pfx = base64.decodestring(certificate)
    certificado = Certificado(cert_pfx, password)
    canc = {
        'motivo': vals['justificativa'],
        'aedf': vals['aedf'],
        'numero': vals['numero'],
        'codigo_verificacao': vals['protocolo_nfe'],
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
    msg_cancelada = 'A Nota Fiscal já está com a situação cancelada.'
    if resposta['status_code'] == 200 or retorno.message == msg_cancelada:
        return {
            'code': 200,
            'message': 'Nota Fiscal Cancelada',
        }
    else:
        return {
            'code': 400,
            'api_code': resposta['status_code'],
            'message': retorno.message,
        }
