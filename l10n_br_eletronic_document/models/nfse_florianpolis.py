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


    if vals['regime_fiscal'] != 'normal':
        vals['base_calculo_iss'] = 0
        vals['valor_iss'] = 0
    return vals


def send_api(certificate, password, vals):
    cert_pfx = base64.decodestring(certificate)
    certificado = Certificado(cert_pfx, password)

    vals = _convert_values(vals)
    recebe_lote = processar_nota(
        certificado, rps=vals, ambiente=self.ambiente,
        client_id=self.company_id.client_id,
        secret_id=self.company_id.client_secret,
        username=self.company_id.inscr_mun,
        password=self.company_id.user_password)

    retorno = recebe_lote['object']
    if "codigoVerificacao" in dir(retorno):
        return { 
            'code': 201,
            'entity': {
                'codigo_verificacao': retorno.codigoVerificacao,
                'numero_nfse': retorno.numero_nfse,
            }
        }
    else:
        return { 
            'code': 400,
            'entity': {
                'codigo': recebe_lote['status_code'],
                'mensagem': retorno.messagf,
            }
        }

def cancel_api(certificate, password, vals)
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
