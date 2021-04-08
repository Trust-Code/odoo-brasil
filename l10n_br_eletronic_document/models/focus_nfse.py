import json
import base64
import requests
import logging
from urllib.parse import urlparse


_logger = logging.getLogger(__name__)


def _convert_values(vals):

    aliquota_iss = vals["itens_servico"][0]["aliquota"]

    vals["servico"] = {
        "item_lista_servico": vals["itens_servico"][0]["codigo_servico"],
        "codigo_tributario_municipio": vals["itens_servico"][0][
            "codigo_servico_municipio"
        ],
        "aliquota": abs(aliquota_iss),
        "iss_retido": False if aliquota_iss >= 0 else True,
        "valor_iss": vals["valor_iss"] if vals['valor_iss'] >= 0 else 0,
        "valor_iss_retido": abs(vals["valor_iss"]) if vals['valor_iss'] < 0 else 0,
        "valor_inss": vals["inss_valor_retencao"],
        "valor_servicos": vals["valor_servico"],
        "discriminacao": vals["discriminacao"],
    }
    vals["natureza_operacao"] = "1"
    vals["prestador"] = vals["emissor"]
    if len(vals["tomador"]["cnpj_cpf"]) == 14:
        vals["tomador"]["cnpj"] = vals["tomador"]["cnpj_cpf"]
    elif len(vals["tomador"]["cnpj_cpf"]) == 11:
        vals["tomador"]["cpf"] = vals["tomador"]["cnpj_cpf"]
    if vals['regime_tributario'] == 'simples':
        vals['regime_especial_tributacao'] = 6
        vals['optante_simples_nacional'] = True
    return vals


def send_api(token, ambiente, edocs):
    edocs = _convert_values(edocs[0])

    if ambiente == "producao":
        url = "https://api.focusnfe.com.br/v2/nfse"
    else:
        url = "https://homologacao.focusnfe.com.br/v2/nfse"

    ref = {"ref": edocs["nfe_reference"]}
    response = requests.post(url, params=ref, data=json.dumps(edocs), auth=(token, ""))
    if response.status_code in (401, 500):
        _logger.error("Erro ao enviar NFe Focus\n%s" + response.text)
        _logger.info(json.dumps(edocs))
        return {
            "code": 400,
            "api_code": 500,
            "message": "Erro ao tentar envio de NFe - Favor contactar suporte\n%s" % response.text,
        }

    response = response.json()
    if response.get("status", False) == "processando_autorizacao":
        return {
            "code": "processing",
            "message": "Nota Fiscal em processamento",
        }
    else:
        return {
            "code": 400,
            "api_code": response["codigo"],
            "message": response["mensagem"],
        }


def _download_file(pdf_path):
    response = requests.get(pdf_path)
    return response.content


def check_nfse_api(token, ambiente, nfe_reference):
    if ambiente == "producao":
        url = "https://api.focusnfe.com.br/v2/nfse/" + nfe_reference
    else:
        url = "https://homologacao.focusnfe.com.br/v2/nfse/" + nfe_reference

    response = requests.get(url, auth=(token, "")).json()
    if response.get("status", False) == "processando_autorizacao":
        return {
            "code": "processing",
        }
    elif response.get("status", False) == "autorizado":
        pdf = _download_file(response["url_danfse"])

        o = urlparse(response["url"])
        xml_path = '%s://%s%s' % (o.scheme, o.hostname, response["caminho_xml_nota_fiscal"])
        xml = _download_file(xml_path)
        return {
            "code": 201,
            "entity": {
                "protocolo_nfe": response["codigo_verificacao"],
                "numero_nfe": int(response["numero"][4:]),
            },
            "pdf": pdf,
            "xml": xml,
            "url_nfe": response["url"],
        }
    elif response.get("status", False) == "erro_autorizacao":
        return {
            "code": 400,
            "api_code": " ".join([x["codigo"] for x in response["erros"]]),
            "message": "\n".join([x["mensagem"] for x in response["erros"]]),
        }


def cancel_api(token, ambiente, nfe_reference):
    if ambiente == "producao":
        url = "https://api.focusnfe.com.br/v2/nfse/" + nfe_reference
    else:
        url = "https://homologacao.focusnfe.com.br/v2/nfse/" + nfe_reference

    response = requests.delete(url, auth=(token, "")).json()
    if response["status"] in ("cancelado", "nfe_cancelada"):
        return {
            "code": 200,
            "message": "Nota Fiscal Cancelada",
        }
    else:
        return {
            "code": 400,
            "api_code": response["erros"][0]["codigo"],
            "message": response["erros"][0]["mensagem"],
        }
