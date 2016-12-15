# -*- coding: utf-8 -*-
# © 2016 Alessandro Fernandes Martini <alessandrofmartini@gmail.com>, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import base64
import logging
import re
from datetime import datetime
from odoo import api, fields, models
from odoo.exceptions import UserError
_logger = logging.getLogger(__name__)
try:
    from pytrustnfe.nfe import recepcao_evento_carta_correcao
    from pytrustnfe.certificado import Certificado
except (ImportError, IOError) as err:
    _logger.debug(err)


class WizardCartaCorrecaoEletronica(models.TransientModel):
    _name = 'wizard.carta.correcao.eletronica'

    correcao = fields.Text(string="Correção", max_length=1000)
    invoice_id = fields.Many2one('invoice.eletronic', string="Cobrança")

    def valida_carta_correcao_eletronica(self, **kwargs):
        if len(kwargs.get('xCorrecao', '')) < 15:
            raise UserError('Motivo de Correção deve ter mais de ' +
                            '15 caracteres')
        if len(kwargs.get('xCorrecao', '')) > 1000:
            raise UserError('Motivo de Correção deve ter menos de ' +
                            '1000 caracteres')

    @api.multi
    def send_letter(self):
        carta = {}
        invoice_id = self.invoice_id
        carta['invoice_id'] = invoice_id.id
        eventos = self.env['carta.correcao.eletronica.evento']
        cnpj_cpf = re.sub(r"\D", '', self.env.user.company_id.cnpj_cpf)
        carta['CNPJ'] = cnpj_cpf
        carta['CPF'] = ''
        carta['cOrgao'] = self.env.user.company_id.state_id.ibge_code
        carta['tpAmb'] = invoice_id.company_id.tipo_ambiente
        now = datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S')
        carta['dhEvento'] = fields.Datetime.from_string(now)
        carta['chNFe'] = invoice_id.chave_nfe
        carta['xCorrecao'] = self.correcao
        carta['tpEvento'] = '110110'
        self.valida_carta_correcao_eletronica(**carta)
        evento = eventos.create(carta)
        carta['idLote'] = evento.id
        carta['nSeqEvento'] = str(evento.search_count(
            [('invoice_id', '=', invoice_id.id)]))
        carta['Id'] = "ID" + carta['tpEvento'] + carta['chNFe'] +\
            carta['nSeqEvento']
        evento.update(carta)

        cert = invoice_id.company_id.with_context({'bin_size': False}).\
            nfe_a1_file
        cert_pfx = base64.decodestring(cert)
        certificado = Certificado(cert_pfx,
                                  invoice_id.company_id.nfe_a1_password)
        carta['estado'] = self.env.user.company_id.state_id.ibge_code
        carta['ambiente'] = int(invoice_id.company_id.tipo_ambiente)
        resposta = recepcao_evento_carta_correcao(certificado, **carta)
        invoice_id._create_attachment('carta_correcao', invoice_id,
                                      resposta['sent_xml'])
