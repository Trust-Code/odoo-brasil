# -*- coding: utf-8 -*-
# © 2015 Danimar Ribeiro <danimaribeiro@gmail.com>, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


import base64
from datetime import datetime
from odoo import models, api, fields
from odoo.exceptions import ValidationError
from ..service.mde import exec_download_nfe, send_event


class NfeMde(models.Model):
    _name = 'nfe.mde'
    _rec_name = 'numero_sequencial'
    _inherit = [
        'ir.needaction_mixin'
    ]

    @api.multi
    def name_get(self):
        return [(rec.id,
                 u"NFº: {0} ({1}): {2}".format(
                     rec.numero_nfe, rec.cnpj_fornecedor, rec.razao_social)
                 ) for rec in self]

    def _default_company(self):
        return self.env.user.company_id

    company_id = fields.Many2one('res.company', string="Empresa",
                                 default=_default_company, readonly=True)
    currency_id = fields.Many2one(related='company_id.currency_id',
                                  string='Moeda', readonly=True)
    chave_nfe = fields.Char(string="Chave de Acesso", size=50, readonly=True)
    numero_nfe = fields.Char(string="Número NFe", size=10, readonly=True)
    numero_sequencial = fields.Char(
        string="Número Sequencial", readonly=True, size=20)
    cnpj_fornecedor = fields.Char(string="CNPJ", readonly=True, size=20)
    inscricao_estadual = fields.Char(string="RG/IE", readonly=True, size=20)
    razao_social = fields.Char(string="Razão Social", readonly=True, size=200)
    partner_id = fields.Many2one('res.partner', string='Fornecedor')
    data_emissao = fields.Datetime(string="Data Emissão", readonly=True)
    tipo_operacao = fields.Selection(
        [('0', 'Entrada'), ('1', 'Saída')],
        string="Tipo de Operação", readonly=True)
    valor_nfe = fields.Float(
        string="Valor Total da NF-e", readonly=True, digits=(18, 2))
    situacao_nfe = fields.Selection(
        [('1', 'Autorizada'), ('2', 'Cancelada'), ('3', 'Denegada')],
        string="Situação da NF-e", readonly=True)
    state = fields.Selection(string="Situação da Manifestação", readonly=True,
                             selection=[
                                 ('pending', 'Pendente'),
                                 ('ciente', 'Ciente da operação'),
                                 ('confirmado', 'Confirmada operação'),
                                 ('desconhecido', 'Desconhecimento'),
                                 ('nao_realizado', 'Não realizado')
                             ])
    forma_inclusao = fields.Char(string="Forma de Inclusão", readonly=True)
    data_inclusao = fields.Datetime(string="Data de Inclusão", readonly=True)
    eletronic_event_ids = fields.One2many(
        'invoice.eletronic.event', 'nfe_mde_id', string=u"Eventos",
        readonly=True)

    @api.one
    @api.constrains('cnpj_fornecedor', 'partner_id')
    def _check_partner_id(self):
        if self.partner_id and \
           self.cnpj_fornecedor != self.partner_id.cnpj_cpf:
            raise ValidationError(
                "O Parceiro não possui o mesmo CNPJ/CPF do manifesto atual")

    def _needaction_domain_get(self):
        return [('state', '=', 'pending')]

    def _create_event(self, code, message, mde_id):
        return {
            'code': code,
            'message': message,
            'nfe_mde_id': mde_id
        }

    def _create_attachment(self, event, result):
        file_name = 'evento-manifesto-%s.xml' % datetime.now().strftime(
            '%Y-%m-%d-%H-%M')
        self.env['ir.attachment'].create(
            {
                'name': file_name,
                'datas': base64.b64encode(result['received_xml']),
                'datas_fname': file_name,
                'description': u'Evento Manifesto Destinatário',
                'res_model': 'l10n_br_account.document_event',
                'res_id': event.id
            })

    @api.one
    def action_known_emission(self):
        nfe_result = send_event(
            self.company_id, self.chave_nfe, 'ciencia_operacao', self.id)
        env_events = self.env['invoice.eletronic.event']

        event = self._create_event(
            nfe_result['code'], nfe_result['message'], self.id)

        if nfe_result['code'] == '135':
            self.state = 'ciente'
        elif nfe_result['code'] == '573':
            self.state = 'ciente'
            event['response'] = 'Ciência da operação já previamente realizada'
        else:
            event['response'] = 'Ciência da operação sem êxito'

        event = env_events.create(event)
        self._create_attachment(event, nfe_result)
        return True

    @api.one
    def action_confirm_operation(self):
        nfe_result = send_event(
            self.company_id, self.chave_nfe, 'confirma_operacao', self.id)
        env_events = self.env['invoice.eletronic.event']

        event = self._create_event(
            nfe_result['code'], nfe_result['message'], self.id)

        if nfe_result['code'] == '135':
            self.state = 'confirmado'
        else:
            event['response'] = 'Confirmação da operação sem êxito'

        event = env_events.create(event)
        self._create_attachment(event, nfe_result)
        return True

    @api.one
    def action_unknown_operation(self):
        nfe_result = send_event(
            self.company_id,
            self.chave_nfe,
            'desconhece_operacao',
            self.id)
        env_events = self.env['invoice.eletronic.event']

        event = self._create_event(
            nfe_result['code'], nfe_result['message'], self.id)

        if nfe_result['code'] == '135':
            self.state = 'desconhecido'
        else:
            event['response'] = 'Desconhecimento da operação sem êxito'

        event = env_events.create(event)
        self._create_attachment(event, nfe_result)
        return True

    @api.one
    def action_not_operation(self):
        nfe_result = send_event(
            self.company_id,
            self.chave_nfe,
            'nao_realizar_operacao')
        env_events = self.env['invoice.eletronic.event']

        event = self._create_event(
            nfe_result['code'], nfe_result['message'], self.id)

        if nfe_result['code'] == '135':
            self.state = 'nap_realizado'
        else:
            event['response'] = 'Tentativa de Operação não realizada sem êxito'

        event = env_events.create(event)
        self._create_attachment(event, nfe_result)
        return True

    @api.one
    def action_download_xml(self):
        nfe_result = exec_download_nfe(self.company_id, [self.chave_nfe])
        env_events = self.env['invoice.eletronic.event']

        if nfe_result['code'] == '140':
            event = self._create_event(
                nfe_result['code'], nfe_result['message'], self.id)
            env_events.create(event)
            file_name = 'NFe%s.xml' % self.chave_nfe
            self.env['ir.attachment'].create(
                {
                    'name': file_name,
                    'datas': base64.b64encode(nfe_result['file_returned']),
                    'datas_fname': file_name,
                    'description':
                    u'XML NFe - Download manifesto do destinatário',
                    'res_model': 'nfe.mde',
                    'res_id': self.id
                })

        else:
            event = self._create_event('Download NFe não efetuado', nfe_result,
                                       type_event='10')
            event = env_events.create(event)
            self._create_attachment(event, nfe_result)
        return True
