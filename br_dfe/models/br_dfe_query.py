# -*- coding: utf-8 -*-

import base64, re, logging, zlib, pytz
from lxml import etree, objectify
from datetime import datetime
from odoo import models, fields, api, exceptions, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DTFT

_logger = logging.getLogger(__name__)

try:
    from pytrustnfe.nfe import xml_consulta_distribuicao_nfe
    from pytrustnfe.nfe import consulta_distribuicao_nfe
    from pytrustnfe.nfe import xml_download_nfe
    from pytrustnfe.nfe import download_nfe
    from pytrustnfe.nfe import xml_recepcao_evento_manifesto
    from pytrustnfe.nfe import recepcao_evento_manifesto
    from pytrustnfe.certificado import Certificado

except ImportError:
    _logger.info('Cannot import pytrustnfe', exc_info=True)

class SpedDFeQuery(models.Model):

    _name = 'sped.dfe.query'

    name = fields.Char()
    ultNSU = fields.Char(string='Último NSU', readonly=True)
    maxNSU = fields.Char(string='Maior NSU', readonly=True)
    lowest_nsu = fields.Integer(string='Menor NSU Biaxado')
    greater_nsu = fields.Integer(string='Maior NSU Biaxado')
    dhResp = fields.Char(string='Data e Hora da Resposta', readonly=True)
    xml_received = fields.Binary(string='XML da Consulta', readonly=True)
    xml_name = fields.Char()
    nsu_ids = fields.Many2many('sped.dfe.query.nsu', 'sped_dfe_results_nsu')

class SpedDFeQueryNSU(models.Model):

    _name = 'sped.dfe.query.nsu'

    company_id = fields.Many2one('res.company', u'Empresa', index=True, readonly=True)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', string="Moeda")
    name = fields.Char('Nome', compute='_compute_name')
    query_ids = fields.Many2many('sped.dfe.query', 'sped_dfe_results_nsu', readonly=True)
    event_line = fields.One2many('sped.dfe.query.nsu.event', 'nsu_id', string='Registro de Eventos',
                                 copy=False, readonly=True, auto_join=True)
    nsu = fields.Integer(string='Seq. Único', readonly=True)
    nsu_type = fields.Selection([('res_nfe', 'Resumo NF-e'), ('nfe', 'Nota Fiscal'), ('res_evento', 'Resumo de Evento'),
                                 ('proc_evento', 'Manifestação do Cliente')],string='Tipo de Evento',
                                store=True, readonly=True)
    partner_id = fields.Many2one('res.partner', compute='_search_partner', string='Parceiro no Sistema',readonly=True,
                                 store=True)
    evento_manifestado = fields.Boolean('Manifestado', compute='_search_manifesto', default=False)
    data_evento = fields.Date(string='Data do Evento', readonly=True)
    nfe_relacionada = fields.Many2one('invoice.eletronic', compute='_search_nfe', string='Nota Fiscal Relacionada')
    xnome = fields.Char(string='Nome do Emitente', readonly=True)
    parent_id = fields.One2many('sped.dfe.query.nsu', string='Seq. Relacionado(s)', index=True, compute='_compute_parents')
    cnpj = fields.Char(string='CNPJ do Emitente', readonly=True)
    ie = fields.Char(string='Insc Est', readonly=True)
    xml = fields.Binary(string='XML do Documento', readonly=True)
    xml_name = fields.Char(readonly=True)
    chave_nfe = fields.Char(string='Chave do Documento Eletrônico', readonly=True)
    tpnf = fields.Char(string='Tipo da NF-e', readonly=True)
    cod_evento = fields.Char(string='Código do Evento', readonly=True)
    nome_evento = fields.Char(string='Nome do Evento', readonly=True)
    valor_nfe = fields.Float(string='Valor', readonly=True, digits=(8, 2))
    nfe_xml = fields.Binary(string='XML da NF-e', readonly=True)

    _sql_constraints = [
        ('sped_dfe_query_nsu_nsu_uniq', 'unique (nsu)',
         _(u'Não podem haver mais de um registro por NSU!'))
    ]

    @api.multi
    @api.depends('nsu_type', 'chave_nfe')
    def _search_manifesto(self):
        for record in self:
            if record.event_line.nsu_id:
                record.evento_manifestado = True
            else:
                record.evento_manifestado = False

    @api.multi
    @api.depends('nsu_type', 'chave_nfe')
    def _search_nfe(self):
        for record in self:
            if record.nsu_type == 'proc_evento':
                inv_eletronic = self.env['invoice.eletronic'].search([('chave_nfe','=',record.chave_nfe)])
                record.nfe_relacionada = inv_eletronic.id

    @api.multi
    def _compute_name(self):
        for record in self:
            if record.nome_evento != False:
                name = str(record.nsu) + ' - ' + record.nome_evento
            elif record.nsu_type == 'nfe':
                name = str(record.nsu) + ' - NF-e'
            elif record.nsu_type == 'res_nfe':
                name = str(record.nsu) + ' - Resumo de NF-e'
            else:
                name = str(record.nsu) + ' - NSU'
            record.name = name

    @api.multi
    def _compute_parents(self):
        for record in self:
            if record.chave_nfe != None:
                nsu = []
                nsu_rel = self.env['sped.dfe.query.nsu'].search([('chave_nfe', '=', record.chave_nfe),
                                                                 ('id', '!=', record.id)])
                for n in nsu_rel:
                    nsu.append(n.id)
                record.parent_id = [(6, 0, list(nsu))]

    @api.multi
    @api.depends('cnpj')
    def _search_partner(self):
        self.ensure_one()
        if not self.cnpj:
            return
        val = re.sub('[^0-9]', '', self.cnpj)
        if len(val) == 14:
            cnpj_cpf = "%s.%s.%s/%s-%s" \
                       % (val[0:2], val[2:5], val[5:8], val[8:12], val[12:14])
        elif len(val) == 11:
            cnpj_cpf = "%s.%s.%s-%s" \
                       % (val[0:3], val[3:6], val[6:9], val[9:11])

        partner = self.env['res.partner'].search([('cnpj_cpf', '=', cnpj_cpf)])
        if partner.id:
            self.partner_id = partner.id
        else:
            partner = self.env['res.partner'].search([('cnpj_cpf', '=', self.cnpj)])
            self.partner_id = partner.id

    @api.multi
    def confirm_operation(self):
        company_id = self.env['res.company']._company_default_get('account.account')
        res = []
        for record in self:
            manifest = self.env['sped.manifest.wizard'].create({
                'company_id': company_id.id,
                'cnpj_cpf': company_id.cnpj_cpf,
                'ambiente': company_id.tipo_ambiente,
                'chave_nfe': record.chave_nfe,
                'event_code': '210200',
                'nsu': record.nsu,
                })
            manifestar = manifest.send_manifesto()
            res.append(manifestar)

        mensagem = ''
        for message in res:
            mensagem += message + '\n'

        return {
            'name': 'Messagem',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'sped.dfe.query.cstat',
            'target': 'new',
            'context': { 'default_message': mensagem }
        }

    @api.multi
    def deny_operation(self):
        company_id = self.env['res.company']._company_default_get('account.account')
        res = []
        for record in self:
            manifest = self.env['sped.manifest.wizard'].create({
                'company_id': company_id.id,
                'cnpj_cpf': company_id.cnpj_cpf,
                'ambiente': company_id.tipo_ambiente,
                'chave_nfe': record.chave_nfe,
                'event_code': '210240',
                'nsu': record.nsu,
                })
            manifestar = manifest.send_manifesto()
            res.append(manifestar)

        mensagem = ''
        for message in res:
            mensagem += message + '\n'

        return {
            'name': 'Messagem',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'sped.dfe.query.cstat',
            'target': 'new',
            'context': { 'default_message': mensagem }
        }




    @api.multi
    def wizard_manifestar_nsu(self):
        for record in self:
            vals = {
                'default_chave_nfe': record.chave_nfe,
                'default_event_code': '210200',
                'default_nsu': record.nsu,
            }

        return {
            'name': 'Manifestar',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'sped.manifest.wizard',
            'target': 'new',
            'context': vals
        }

    @api.multi
    def negar_manifestar_nsu(self):
        for record in self:
            vals = {
                'default_chave_nfe': record.chave_nfe,
                'default_event_code': '210240',
                'default_nsu': record.nsu,
            }

        return {
            'name': 'Manifestar',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'sped.manifest.wizard',
            'target': 'new',
            'context': vals
        }


class SpedManifestWizard(models.TransientModel):

    _name = 'sped.manifest.wizard'

    nsu = fields.Char()
    company_id = fields.Many2one('res.company', u'Empresa', readonly=True,
                                 default=lambda self: self.env['res.company']._company_default_get('account.account'))
    ambiente = fields.Selection([('homologacao', 'Homologação'), ('producao', 'Produção')], readonly=True,
                                string='Ambiente de Consulta', related='company_id.tipo_ambiente')
    cnpj_cpf = fields.Char(string='CNPJ/CPF', related='company_id.cnpj_cpf')
    chave_nfe = fields.Char(string='Chave do Documento Eletrônico')
    event_code = fields.Selection([('210200', 'Confirmação da Operação'),('210210', 'Ciência da Operação'),
                                    ('210220', 'Desconhecimento da Operação'),('210240', 'Operação não Realizada')],
                                  string='Evento')
    event_description = fields.Char(string='Descrição do Evento', compute='compute_event_description')
    justificativa = fields.Char(string='Justificativa do Evento')

    @api.depends('event_code')
    def compute_event_description(self):
        for record in self:
            if record.event_code == '210200':
                record.event_description = 'Confirmação da Operação'
            elif record.event_code == '210210':
                record.event_description = 'Ciência da Operação'
            elif record.event_code == '210220':
                record.event_description = 'Desconhecimento da Operação'
            elif record.event_code == '210240':
                record.event_description = 'Operação não Realizada'

    @api.multi
    def _prepare_manifest_vals(self):
        tz = pytz.timezone(self.env.user.partner_id.tz) or pytz.utc
        dt_evento = datetime.utcnow()
        dt_evento = pytz.utc.localize(dt_evento).astimezone(tz)
        data = dt_evento.strftime('%Y-%m-%dT%H:%M:%S%z')
        data = '%s' %(data[0:22]+':'+data[22:24])
        for record in self:
            identificador = 'ID' + str(record.event_code) + str(record.chave_nfe) + '01'
            vals = {
                'lote': record.id,
                'ambiente': record.ambiente,
                'manifesto': {
                    'identificador': identificador,
                    'cnpj_empresa': re.sub('[^0-9]', '', record.cnpj_cpf),
                    'chave_nfe': record.chave_nfe,
                    'data_hora_evento': data,
                    'event_code': record.event_code,
                    'numero_sequencial': 1,
                    'event_description': record.event_description,
                },
            }

            if record.event_code == '210240':
                vals['justificativa'] = record.justificativa

        return vals

    @api.multi
    def send_manifesto(self):
        manifesto = self._prepare_manifest_vals()
        cert = self.company_id.with_context({'bin_size': False}).nfe_a1_file
        cert_pfx = base64.decodestring(cert)
        certificado = Certificado(cert_pfx, self.company_id.nfe_a1_password)
        xml_to_send = xml_recepcao_evento_manifesto(certificado, **manifesto)

        resposta = recepcao_evento_manifesto(certificado, estado=self.company_id.partner_id.state_id.ibge_code,
                                             ambiente=1 if self.ambiente == '1' else 2, modelo='consulta',
                                             xml=xml_to_send)

        retorno = resposta['object'].Body.nfeRecepcaoEventoResult.getchildren()[0]

        if retorno.cStat == 128:

            xml_received = base64.b64encode(bytes(resposta['received_xml'], 'utf-8'))

            for evento in retorno.retEvento.infEvento:
                event = self.env['sped.dfe.query.nsu.event']
                nsu = self.env['sped.dfe.query.nsu'].search([('chave_nfe', '=', evento.chNFe),('nsu','=',self.nsu)])
                vals_evento = {
                    'nsu_id': nsu.id,
                    'code': evento.tpEvento,
                    'name': evento.xEvento,
                    'dt_evento': evento.dhRegEvento,
                    'xml_file': xml_received,
                }
                if evento.find('nProt') != None:
                    vals_evento['protocolo'] = evento.nProt

                event.create(vals_evento)

        mensagem = str(retorno.cStat) + ' - ' + str(retorno.xMotivo)

        return mensagem

class SpedDFeQueryNSUEvent(models.Model):

    _name = 'sped.dfe.query.nsu.event'

    nsu_id = fields.Many2one('sped.dfe.query.nsu', string='NSU', required=True,
                               ondelete='cascade', index=True, copy=False, readonly=True)
    code = fields.Char(string='Código do Evento', readonly=True)
    name = fields.Char(string='Descrição do Evento', readonly=True)
    protocolo = fields.Char(string='Protocolo', readonly=True)
    dt_evento = fields.Char(string='Data e Hora', readonly=True)
    xml_file = fields.Binary(readonly=True)
    xml_name = fields.Char(readonly=True)