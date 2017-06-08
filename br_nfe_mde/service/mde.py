# -*- coding: utf-8 -*-
# © 2015 Danimar Ribeiro <danimaribeiro@gmail.com>, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import re
import base64
import gzip
import cStringIO
import logging
from datetime import datetime

_logger = logging.getLogger(__name__)

try:
    from pytrustnfe.certificado import Certificado
    from pytrustnfe.nfe import consulta_distribuicao_nfe
    from pytrustnfe.nfe import recepcao_evento_manifesto
except ImportError:
    _logger.info('Cannot import pytrustnfe', exc_info=True)


def __certificado(company):
    cert = company.with_context({'bin_size': False}).nfe_a1_file
    cert_pfx = base64.decodestring(cert)
    certificado = Certificado(cert_pfx, company.nfe_a1_password)
    return certificado


def _format_nsu(nsu):
    nsu = long(nsu)
    return "%015d" % (nsu,)


def distribuicao_nfe(company, ultimo_nsu):
    ultimo_nsu = _format_nsu(ultimo_nsu)
    certificado = __certificado(company)
    cnpj_partner = re.sub('[^0-9]', '', company.cnpj_cpf)
    consulta = dict(
        cnpj_cpf=cnpj_partner,
        ultimo_nsu=ultimo_nsu,
    )
    result = consulta_distribuicao_nfe(
        consulta=consulta,
        estado=company.partner_id.state_id.ibge_code,
        certificado=certificado,
        ambiente=1 if company.tipo_ambiente == 'producao' else 2
    )

    retorno = result['object'].Body.nfeDistDFeInteresseResponse
    retorno = retorno.nfeDistDFeInteresseResult.retDistDFeInt

    if retorno.cStat == 138:
        nfe_list = []
        for doc in retorno.loteDistDFeInt.docZip:
            orig_file_desc = gzip.GzipFile(
                mode='r',
                fileobj=cStringIO.StringIO(
                    base64.b64decode(str(doc)))
            )
            orig_file_cont = orig_file_desc.read()
            orig_file_desc.close()

            nfe_list.append({
                'xml': orig_file_cont, 'schema': doc.attrib['schema'],
                'NSU': doc.attrib['NSU']
            })

        return {
            'code': retorno.cStat,
            'message': retorno.xMotivo,
            'list_nfe': nfe_list, 'file_returned': result['received_xml']
        }
    else:
        return {
            'code': retorno.cStat,
            'message': retorno.xMotivo,
            'file_sent': result['sent_xml'],
            'file_returned': result['received_xml']
        }


def send_event(company, nfe_key, method, lote):
    certificado = __certificado(company)
    cnpj_partner = re.sub('[^0-9]', '', company.cnpj_cpf)
    result = {}

    ide = "ID%s%s%s" % ('210200', nfe_key, '01')
    manifesto = {
        'cnpj_empresa': cnpj_partner,
        'chave_nfe': nfe_key,
        'data_hora_evento': datetime.now().strftime('%Y-%m-%dT%H:%M:%S-00:00'),
        'numero_sequencial': 1,
        'identificador': ide
    }
    result = recepcao_evento_manifesto(
        certificado=certificado,
        evento=method,
        manifesto=manifesto,
        ambiente=1 if company.tipo_ambiente == 'producao' else 2,
        lote=lote,
        estado=company.partner_id.state_id.ibge_code,
    )

    if result.resposta.status == 200:  # Webservice ok
        if result.resposta.cStat.valor == '128':
            inf_evento = result.resposta.retEvento[0].infEvento
            return {
                'code': inf_evento.cStat.valor,
                'message': inf_evento.xMotivo.valor,
                'file_sent': result.envio.xml,
                'file_returned': result.resposta.xml
            }
        else:
            return {
                'code': result.resposta.cStat.valor,
                'message': result.resposta.xMotivo.valor,
                'file_sent': result.envio.xml,
                'file_returned': result.resposta.xml
            }
    else:
        return {
            'code': result.resposta.status,
            'message': result.resposta.reason,
            'file_sent': result.envio.xml,
            'file_returned': None
        }


def exec_download_nfe(company, list_nfe):
    certificado = __certificado(company)
    cnpj_partner = re.sub('[^0-9]', '', company.cnpj_cpf)
    result = consulta_distribuicao_nfe(
        estado=company.partner_id.state_id.ibge_code,
        certificado=certificado,
        ambiente=1 if company.tipo_ambiente == 'producao' else 2,
        cnpj=cnpj_partner,
        lista_chaves=list_nfe)

    if result.resposta.status == 200:  # Webservice ok
        if result.resposta.cStat.valor == '139':
            nfe = result.resposta.retNFe[0]
            if nfe.cStat.valor == '140':
                return {
                    'code': nfe.cStat.valor, 'message': nfe.xMotivo.valor,
                    'file_sent': result.envio.xml,
                    'file_returned': nfe.procNFe.valor.encode('utf-8'),
                    'nfe': nfe
                }
            else:
                return {
                    'code': nfe.cStat.valor, 'message': nfe.xMotivo.valor,
                    'file_sent': result.envio.xml,
                    'file_returned': result.resposta.xml
                }

        else:
            return {
                'code': result.resposta.cStat.valor,
                'message': result.resposta.xMotivo.valor,
                'file_sent': result.envio.xml,
                'file_returned': result.resposta.xml
            }
    else:
        return {
            'code': result.resposta.status, 'message': result.resposta.reason,
            'file_sent': result.envio.xml, 'file_returned': None
        }
