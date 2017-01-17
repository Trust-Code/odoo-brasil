# -*- coding: utf-8 -*-
# © 2016 Alessandro Martini <alessandrofmartini@gmail.com>, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import base64
import logging
from datetime import datetime

from odoo import api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

try:
    from pytrustnfe.nfe import inutilizar_nfe
    from pytrustnfe.certificado import Certificado
except ImportError:
    _logger.debug('Cannot import pytrustnfe', exc_info=True)


class InutilizationNFeNumeration(models.TransientModel):
    _name = 'wizard.inutilization.nfe.numeration'

    numeration_start = fields.Integer('Começo da Numeração', required=True)
    numeration_end = fields.Integer('Fim da Numeração', required=True)
    serie = fields.Many2one('br_account.document.serie', string='Série',
                            required=True)
    modelo = fields.Selection([
        ('55', '55 - NFe'),
        ('65', '65 - NFCe'), ],
        string='Modelo', required=True)
    justificativa = fields.Text(
        'Justificativa', required=True,
        help='Mínimo: 15 caracteres;\nMáximo: 255 caracteres.')

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
        if len(self.justificativa) < 15:
            errors.append('A Justificativa deve ter no mínimo 15 caracteres')
        if len(self.justificativa) > 255:
            errors.append('A Justificativa deve ter no máximo 255 caracteres')
        if len(errors):
            raise UserError('\n'.join(errors))

    def create_inutilized(self):
        name = 'Série Inutilizada {inicio} - {fim}'.format(
            inicio=self.numeration_start, fim=self.numeration_end
        )
        self.env['invoice.eletronic.inutilized'].create(dict(
            name=name,
            numero_inicial=self.numeration_start,
            numero_final=self.numeration_end,
            justificativa=self.justificativa,
        ))

    def _prepare_obj(self, company, estado, ambiente):
        ano = str(datetime.now().year)[2:]
        serie = self.serie.code.zfill(3)
        ID = ('ID{ambiente:.1}{estado:.2}{ano:.2}{cnpj:.14}{modelo:.2}'
              '{serie:.3}{num_inicial:09}{num_final:09}')
        ID = ID.format(ambiente=ambiente, estado=estado, ano=ano,
                       cnpj=company.cnpj_cpf, modelo=self.modelo, serie=serie,
                       num_inicial=self.numeration_start,
                       num_final=self.numeration_end)
        return {
            'id': ID,
            'ambiente': ambiente,
            'estado': estado,
            'ano': ano,
            'cnpj': company.cnpj_cpf,
            'modelo': self.modelo,
            'serie': serie,
            'numero_inicio': self.numeration_start,
            'numero_fim': self.numeration_end,
            'justificativa': self.justificativa,
        }

    def _handle_resposta(self, resposta):
        inutilized_obj = self.env['invoice.eletronic.inutilized'].search([
            ('numero_inicial', '=', self.numeration_start),
            ('numero_final', '=', self.numeration_end),
            ('justificativa', '=', self.justificativa)
        ], limit=1)
        inutilized_obj._create_attachment('inutilizacao-envio', inutilized_obj,
                                          resposta['sent_xml'])
        inutilized_obj._create_attachment('inutilizacao-recibo',
                                          inutilized_obj,
                                          resposta['received_xml'])

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
    def action_inutilize_nfe(self):
        self.validate_hook()
        self.create_inutilized()
        self.send_sefaz()
