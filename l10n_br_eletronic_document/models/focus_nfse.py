import json
import base64
import requests


def _convert_values(vals):
    vals['servico'] = {
        'item_lista_servico': vals['itens_servico'][0]['codigo_servico'],
        'codigo_tributario_municipio': vals['itens_servico'][0]['codigo_servico_municipio'],
        "aliquota": vals['itens_servico'][0]['aliquota'],
        "valor_servicos": vals['valor_servico'],
        "discriminacao": vals['discriminacao'],
    }
    vals['prestador'] = vals['emissor']
    vals['tomador']['cnpj'] = vals['tomador']['cnpj_cpf']
    return vals


def send_api(certificate, password, token, ambiente, edocs):
    cert_pfx = base64.decodestring(certificate)

    edocs = _convert_values(edocs[0])

    if ambiente == 'producao':
        url = 'https://api.focusnfe.com.br/v2/nfse'
    else:
        url = 'https://homologacao.focusnfe.com.br/v2/nfse'

    ref = {'ref': edocs['nfe_reference']}
    response = requests.post(url, params=ref, data=json.dumps(
        edocs), auth=(token, "")).json()
    if response.get('status', False) == 'processando_autorizacao':
        return {
            'code': 200,
            'message': 'Nota Fiscal em processamento',
        }
    else:
        return {
            'code': 400,
            'api_code': response['codigo'],
            'message': response['mensagem'],
        }


def cancel_api(token, ambiente, nfe_reference):
    if ambiente == 'producao':
        url = 'https://api.focusnfe.com.br/v2/nfse/' + nfe_reference
    else:
        url = 'https://homologacao.focusnfe.com.br/v2/nfse/' + nfe_reference

    response = requests.delete(url, auth=(token, "")).json()
    if response['status'] in ('cancelado', 'nfe_cancelada'):
        return {
            'code': 200,
            'message': 'Nota Fiscal Cancelada',
        }
    else:
        return {
            'code': 400,
            'api_code': response['erros'][0]['codigo'],
            'message': response['erros'][0]['mensagem'],
        }
