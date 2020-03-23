import base64
from pytrustnfe.nfse.floripa import xml_processar_nota
from pytrustnfe.nfse.floripa import processar_nota
from pytrustnfe.nfse.floripa import cancelar_nota

from pytrustnfe.certificado import Certificado


def _convert_values(vals):
    cfps = '9201'
    if vals['outra_cidade']:
        cfps = '9202'
    if vals['outro_estado']:
        cfps = '9203'
    vals['cfps'] = cfps

    if vals['regime_tributario'] == 'simples':
        vals['base_calculo'] = 0
        vals['valor_issqn'] = 0
        for item in vals['itens_servico']:
            item['cst_servico'] = '1'
    else:
        vals['valor_issqn'] = vals['valor_iss']
    vals['tomador']['logradouro'] = vals['tomador']['endereco']['logradouro']
    vals['tomador']['numero'] = vals['tomador']['endereco']['numero']
    vals['tomador']['bairro'] = vals['tomador']['endereco']['bairro']
    vals['tomador']['complemento'] = vals['tomador']['endereco']['complemento']
    vals['tomador']['cep'] = vals['tomador']['endereco']['cep']
    vals['tomador']['uf'] = vals['tomador']['endereco']['uf']
    vals['tomador']['cidade'] = vals['tomador']['endereco']['codigo_municipio']
    return vals


def send_api(certificate, password, list_rps):
    cert_pfx = base64.decodestring(certificate)
    certificado = Certificado(cert_pfx, password)

    vals = list_rps[0]
    vals = _convert_values(vals)

    recebe_lote = processar_nota(
        certificado, rps=vals, ambiente=vals['ambiente'],
        client_id=vals['client_id'],
        secret_id=vals['client_secret'],
        username=vals['emissor']['inscricao_municipal'],
        password=vals['user_password'])

    retorno = recebe_lote['object']
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

    company = self.company_id
    canc = {
        'motivo': justificativa,
        'aedf': re.sub('[^0-9]', '', company.aedf),
        'numero': self.numero_nfse,
        'codigo_verificacao': self.verify_code,
    }
    resposta = cancelar_nota(certificado, cancelamento=canc,
                              ambiente=self.ambiente,
                              client_id=self.company_id.client_id,
                              secret_id=self.company_id.client_secret,
                              username=self.company_id.inscr_mun,
                              password=self.company_id.user_password)
    retorno = resposta['object']
    msg_cancelada = 'A Nota Fiscal já está com a situação cancelada.'
    if resposta['status_code'] == 200 or retorno.message == msg_cancelada:
        self.state = 'cancel'
        self.codigo_retorno = '100'
        self.mensagem_retorno = 'Nota Fiscal Cancelada'
    else:
        self.codigo_retorno = resposta['status_code']
        self.mensagem_retorno = retorno.message

    self.env['invoice.eletronic.event'].create({
        'code': self.codigo_retorno,
        'name': self.mensagem_retorno,
        'invoice_eletronic_id': self.id,
    })
    self._create_attachment(
        'canc', self, resposta['sent_xml'])
    self._create_attachment(
        'canc-ret', self, resposta['received_xml'].decode('utf-8'))
