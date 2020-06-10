# -*- coding: utf-8 -*-
# © 2015 Danimar Ribeiro <danimaribeiro@gmail.com>, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import re
import base64
import gzip
import io
import logging
from datetime import datetime

_logger = logging.getLogger(__name__)

try:
    from pytrustnfe.certificado import Certificado
    from pytrustnfe.nfe import consulta_distribuicao_nfe
    from pytrustnfe.nfe import recepcao_evento_manifesto
    from pytrustnfe.nfe import download_nfe
except ImportError:
    _logger.info('Cannot import pytrustnfe', exc_info=True)


def __certificado(company):
    cert = company.with_context({'bin_size': False}).nfe_a1_file
    cert_pfx = base64.decodestring(cert)
    certificado = Certificado(cert_pfx, company.nfe_a1_password)
    return certificado


def _format_nsu(nsu):
    return "%015d" % (int(nsu),)


def distribuicao_nfe(company, ultimo_nsu):
    ultimo_nsu = _format_nsu(ultimo_nsu)
    if company.nfe_a1_file:
        company_cert = company
    elif company.parent_id and company.parent_id.nfe_a1_file:
        company_cert = company.parent_id.nfe_a1_file

    certificado = __certificado(company_cert)
    cnpj_partner = re.sub('[^0-9]', '', company.cnpj_cpf)
    result = consulta_distribuicao_nfe(
        cnpj_cpf=cnpj_partner,
        ultimo_nsu=ultimo_nsu,
        estado=company.partner_id.state_id.ibge_code,
        certificado=certificado,
        ambiente=int(company.tipo_ambiente),
        modelo='55',
    )

    retorno = result['object'].getchildren()[0]

    if retorno.cStat == 138:
        nfe_list = []
        for doc in retorno.loteDistDFeInt.docZip:
            orig_file_desc = gzip.GzipFile(
                mode='r',
                fileobj=io.BytesIO(
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


def send_event(company, nfe_key, method, lote, justificativa=None, **kwargs):
    certificado = __certificado(company)
    cnpj_partner = re.sub('[^0-9]', '', company.cnpj_cpf)
    result = {}

    ide = "ID%s%s%s" % (kwargs['evento']['tpEvento'], nfe_key, '01')
    manifesto = {
        'Id': ide,
        'cOrgao': 91,
        'tpAmb': int(company.tipo_ambiente),
        'CNPJ': cnpj_partner,
        'chNFe': nfe_key,
        'dhEvento': datetime.now().strftime('%Y-%m-%dT%H:%M:%S-00:00'),
        'nSeqEvento': 1,
        'identificador': ide,
        'tpEvento': kwargs['evento']['tpEvento'],
        'descEvento': kwargs['evento']['descEvento'],
        'xJust': justificativa if justificativa else '',
    }
    result = recepcao_evento_manifesto(
        certificado=certificado,
        evento=method,
        eventos=[manifesto],
        ambiente=int(company.tipo_ambiente),
        idLote=lote,
        estado='91',
        modelo='55',
    )

    retorno = result['object'].getchildren()[0]

    if retorno.cStat == 128:
        inf_evento = retorno.retEvento[0].infEvento
        return {
            'code': inf_evento.cStat,
            'message': inf_evento.xMotivo,
            'file_sent': result['sent_xml'],
            'file_returned': result['received_xml']
        }
    else:
        return {
            'code': retorno.cStat,
            'message': retorno.xMotivo,
            'file_sent': result['sent_xml'],
            'file_returned': result['received_xml']
        }


def exec_download_nfe(company, list_nfe):
    certificado = __certificado(company)
    cnpj_partner = re.sub('[^0-9]', '', company.cnpj_cpf)
    result = download_nfe(
        estado=company.partner_id.state_id.ibge_code,
        certificado=certificado,
        ambiente=int(company.tipo_ambiente),
        cnpj_cpf=cnpj_partner,
        chave_nfe=list_nfe[0],
        modelo='55')

    retorno = result['object'].getchildren()[0]

    if retorno.cStat == '139':
        nfe = retorno.retNFe[0]
        if nfe.cStat == '140':
            return {
                'code': nfe.cStat, 'message': nfe.xMotivo.valor,
                'file_sent': result.envio.xml,
                'file_returned': nfe.procNFe.valor.encode('utf-8'),
                'nfe': nfe
            }
        else:
            return {
                'code': nfe.cStat, 'message': nfe.xMotivo.valor,
                'file_sent': result.envio.xml,
                'file_returned': result.resposta.xml
            }

    else:
        return {
            'code': retorno.cStat,
            'message': retorno.xMotivo,
            'file_sent': result['sent_xml'],
            'file_returned': result['received_xml'],
            'object': retorno,
        }
