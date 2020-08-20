import json
import base64
import requests
import logging

_logger = logging.getLogger(__name__)


def _convert_values(vals):
    vals["servico"] = {
        "item_lista_servico": vals["itens_servico"][0]["codigo_servico"],
        "codigo_tributario_municipio": vals["itens_servico"][0][
            "codigo_servico_municipio"
        ],
        "aliquota": vals["itens_servico"][0]["aliquota"],
        "valor_servicos": vals["valor_servico"],
        "discriminacao": vals["discriminacao"],
    }
    vals["natureza_operacao"] = "1"
    vals["prestador"] = vals["emissor"]
    if len(vals["tomador"]["cnpj_cpf"]) == 14:
        vals["tomador"]["cnpj"] = vals["tomador"]["cnpj_cpf"]
    elif len(vals["tomador"]["cnpj_cpf"]) == 11:
        vals["tomador"]["cpf"] = vals["tomador"]["cnpj_cpf"]
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


def _download_pdf(pdf_path):
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
        pdf = _download_pdf(response["url_danfse"])
        return {
            "code": 201,
            "entity": {
                "protocolo_nfe": response["codigo_verificacao"],
                "numero_nfe": int(response["numero"][4:]),
            },
            "pdf": pdf,
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
