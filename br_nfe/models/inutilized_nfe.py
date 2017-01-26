# -*- coding: utf-8 -*-
# © 2016 Alessandro Martini <alessandrofmartini@gmail.com>, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import base64
import logging
import re
from datetime import datetime

from odoo import api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

try:
    from pytrustnfe.nfe import inutilizar_nfe
    from pytrustnfe.certificado import Certificado
except ImportError:
    _logger.debug('Cannot import pytrustnfe', exc_info=True)

STATE = {'edit': [('readonly', False)], 'draft': [('readonly', False)]}


class InutilizedNfe(models.Model):
    _name = 'invoice.eletronic.inutilized'

    name = fields.Char('Nome', required=True, readonly=True, states=STATE)
    numeration_start = fields.Integer('Numero Inicial', required=True,
                                      readonly=True, states=STATE)
    numeration_end = fields.Integer('Numero Final', required=True,
                                    readonly=True, states=STATE)
    justificativa = fields.Text('Justificativa', required=True,
                                readonly=True, states=STATE)
    erro = fields.Text('Erros', readonly=True)
    state = fields.Selection([
        ('draft', 'Provisório'),
        ('done', 'Enviado'),
        ('error', 'Erro'),
        ('edit', 'Editando'), ],
        string=u'State', default='edit', required=True, readonly=True)
    modelo = fields.Selection([
        ('55', '55 - NFe'),
        ('65', '65 - NFCe'), ],
        string='Modelo', required=True, readonly=True, states=STATE)
    serie = fields.Many2one('br_account.document.serie', string='Série',
                            required=True, readonly=True, states=STATE)

    @api.model
    def create(self, vals):
        vals['state'] = 'draft'
        return super(InutilizedNfe, self).create(vals)

    def validate_hook(self):
        errors = []
        docs = self.env['invoice.eletronic'].search([
            ('numero', '>=', self.numeration_start),
            ('numero', '<=', self.numeration_end)
        ])
        if docs:
            errors.append('Não é possível invalidar essa série pois já existem'
                          ' documentos com essa numeração.')
        if self.numeration_start > self.numeration_end:
            errors.append('O Começo da Numeração deve ser menor que o '
                          'Fim da Numeração')
        if self.numeration_start < 0 or self.numeration_end < 0:
            errors.append('Não é possível cancelar uma série negativa.')
        if self.numeration_end - self.numeration_start >= 10000:
            errors.append('Número máximo de numeração a inutilizar ultrapassou'
                          ' o limite.')
        if len(self.justificativa) < 15:
            errors.append('A Justificativa deve ter no mínimo 15 caracteres')
        if len(self.justificativa) > 255:
            errors.append('A Justificativa deve ter no máximo 255 caracteres')
        if not self.env.user.company_id.nfe_a1_file:
            errors.append('A empresa não possui um certificado de NFe '
                          'cadastrado')
        if not self.env.user.company_id.cnpj_cpf:
            errors.append('Cadastre o CNPJ da empresa.')
        estado = self.env.user.company_id.state_id
        if not estado or not estado.ibge_code:
            errors.append('Cadastre o Estado da empresa.')
        if len(errors):
            raise UserError('\n'.join(errors))
        return True

    def _prepare_obj(self, company, estado, ambiente):
        ano = str(datetime.now().year)[2:]
        serie = self.serie.code
        cnpj = re.sub(r'\D', '', company.cnpj_cpf)
        ID = ('ID{estado:2}{ano:2}{cnpj:14}{modelo:2}'
              '{serie:03}{num_inicial:09}{num_final:09}')
        ID = ID.format(estado=estado, ano=ano, cnpj=cnpj, modelo=self.modelo,
                       serie=int(serie), num_inicial=self.numeration_start,
                       num_final=self.numeration_end)
        return {
            'id': ID,
            'ambiente': ambiente,
            'estado': estado,
            'ano': ano,
            'cnpj': cnpj,
            'modelo': self.modelo,
            'serie': serie,
            'numero_inicio': self.numeration_start,
            'numero_fim': self.numeration_end,
            'justificativa': self.justificativa,
        }

    def _handle_resposta(self, resposta):
        self._create_attachment('inutilizacao-envio', self,
                                resposta['sent_xml'])
        self._create_attachment('inutilizacao-recibo', self,
                                resposta['received_xml'])
        if hasattr(resposta['object'].Body, 'Fault'):
            raise UserError('Não foi possível concluir a operação.')
        inf_inut = resposta['object'].Body.nfeInutilizacaoNF2Result.\
            retInutNFe.infInut
        status = inf_inut.cStat
        if status == 102:
            self.state = 'done'
        else:
            self.state = 'error'
            self.erro = inf_inut.xMotivo

    def send_sefaz(self):
        company = self.env.user.company_id
        ambiente = company.tipo_ambiente
        estado = company.state_id.ibge_code

        obj = self._prepare_obj(company=company, estado=estado,
                                ambiente=ambiente)

        cert = company.with_context({'bin_size': False}).nfe_a1_file
        cert_pfx = base64.decodestring(cert)
        certificado = Certificado(cert_pfx, company.nfe_a1_password)

        resposta = inutilizar_nfe(certificado, obj=obj, estado=estado,
                                  ambiente=int(ambiente))
        self._handle_resposta(resposta=resposta)

    @api.multi
    def action_send_inutilization(self):
        self.validate_hook()
        self.send_sefaz()

    def _create_attachment(self, prefix, event, data):
        file_name = '%s-%s.xml' % (
            prefix, datetime.now().strftime('%Y-%m-%d-%H-%M'))
        self.env['ir.attachment'].create(
            {
                'name': file_name,
                'datas': base64.b64encode(data),
                'datas_fname': file_name,
                'description': u'',
                'res_model': 'invoice.eletronic.inutilized',
                'res_id': event.id
            })
