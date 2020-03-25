import re
import base64
from pytrustnfe.nfse.paulistana import envio_lote_rps
from pytrustnfe.nfse.paulistana import teste_envio_lote_rps
from pytrustnfe.nfse.paulistana import cancelamento_nfe
from pytrustnfe.nfse.paulistana import consulta_nfe
from pytrustnfe.certificado import Certificado


def _convert_values(vals):
    result = {'lista_rps': vals}

    for rps in vals:
        result['cpf_cnpj'] = rps['emissor']['cnpj']
        result['data_inicio'] = rps['data_emissao']
        result['data_fim'] = rps['data_emissao']
        result['total_servicos'] = rps['valor_servico']
        result['total_deducoes'] = '0.00'

        rps['prestador'] = rps['emissor']
        rps['tomador']['cpf_cnpj'] = rps['tomador']['cnpj_cpf']
        rps['tomador']['tipo_cpfcnpj'] = 2 if rps['tomador']['empresa'] else 1
        rps['aliquota_atividade'] = "%.3f" % rps['itens_servico'][0]['aliquota']
        rps['codigo_atividade'] = re.sub(
            '[^0-9]', '', rps['itens_servico'][0]['codigo_servico'] or '')
        rps['valor_deducao'] = '0.00'
        rps['descricao'] = rps['discriminacao']
        rps['deducoes'] = []
        rps['iss_retido'] = str(rps['iss_retido']).lower()
        rps['numero'] = rps['numero_rps']

        valor_deducao = 0.0
        cnpj_cpf = rps['tomador']['cnpj_cpf']
        data_envio = rps['data_emissao']
        inscr = rps['emissor']['inscricao_municipal']
        iss_retido = 'S' if rps['iss_valor_retencao'] > 0.0 else 'N'
        tipo_cpfcnpj = rps['tomador']['tipo_cpfcnpj']
        codigo_atividade = rps['codigo_atividade']
        tipo_recolhimento = 'T'  # T – Tributado em São Paulo

        assinatura = '%s%s%s%s%sN%s%015d%015d%s%s%s' % (
            str(inscr).zfill(8),
            rps['serie'].ljust(5),
            str(rps['numero_rps']).zfill(12),
            str(data_envio[0:4] + data_envio[5:7] + data_envio[8:10]),
            str(tipo_recolhimento),
            str(iss_retido),
            round(rps['valor_servico'] * 100),
            round(valor_deducao * 100),
            str(codigo_atividade).zfill(5),
            str(tipo_cpfcnpj),
            str(cnpj_cpf).zfill(14)
        )
        rps['assinatura'] = assinatura
    return result


def send_api(certificate, password, edocs):
    cert_pfx = base64.decodestring(certificate)
    certificado = Certificado(cert_pfx, password)

    nfse_values = _convert_values(edocs)
    if edocs[0]['ambiente'] == 'producao':
        resposta = envio_lote_rps(certificado, nfse=nfse_values)
    else:
        resposta = teste_envio_lote_rps(
            certificado, nfse=nfse_values)
    retorno = resposta['object']
    if retorno.Cabecalho.Sucesso:
        if edocs[0]['ambiente'] == 'producao':
            return {
                'code': 201,
                'entity': {
                    'protocolo_nfe': retorno.ChaveNFeRPS.ChaveNFe.CodigoVerificacao,
                    'numero_nfe': retorno.ChaveNFeRPS.ChaveNFe.NumeroNFe,
                },
                'xml': resposta['sent_xml'].encode('utf-8'),
            }
        else:
            return {
                'code': 201,
                'entity': {
                    'protocolo_nfe': 'homologacao',
                    'numero_nfe': 1000,
                },
                'xml': resposta['sent_xml'].encode('utf-8'),
            }
    else:
        return {
            'code': 400,
            'api_code': retorno.Erro.Codigo,
            'message': retorno.Erro.Descricao,
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
    resposta = cancelar_nota(
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
