# -*- coding: utf-8 -*-
# © 2015 Danimar Ribeiro <danimaribeiro@gmail.com>, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


import base64
from datetime import datetime
from odoo import models, api, fields
from odoo.exceptions import ValidationError
from ..service.mde import download_nfe, send_event


class NfeMde(models.Model):
    _name = 'nfe.mde'
    _rec_name = 'nSeqEvento'
    _inherit = [
        'ir.needaction_mixin'
    ]

    @api.multi
    def name_get(self):
        return [(rec.id,
                 u"NFº: {0} ({1}): {2}".format(
                     rec.nNFe, rec.CNPJ, rec.xNome)
                 ) for rec in self]

    def _default_company(self):
        return self.env.user.company_id

    company_id = fields.Many2one('res.company', string="Empresa",
                                 default=_default_company, readonly=True)
    currency_id = fields.Many2one(related='company_id.currency_id',
                                  string='Moeda', readonly=True)
    chNFe = fields.Char(string="Chave de Acesso", size=50, readonly=True)
    nNFe = fields.Char(string="Número NFe", size=10, readonly=True)
    nSeqEvento = fields.Char(
        string="Número Sequencial", readonly=True, size=20)
    CNPJ = fields.Char(string="CNPJ", readonly=True, size=20)
    IE = fields.Char(string="RG/IE", readonly=True, size=20)
    xNome = fields.Char(string="Razão Social", readonly=True, size=200)
    partner_id = fields.Many2one('res.partner', string='Fornecedor')
    dEmi = fields.Datetime(string="Data Emissão", readonly=True)
    tpNF = fields.Selection([('0', 'Entrada'), ('1', 'Saída')],
                            string="Tipo de Operação", readonly=True)
    vNF = fields.Float(string="Valor Total da NF-e",
                       readonly=True, digits=(18, 2))
    cSitNFe = fields.Selection([('1', 'Autorizada'), ('2', 'Cancelada'),
                                ('3', 'Denegada')],
                               string="Situação da NF-e", readonly=True)
    state = fields.Selection(string="Situação da Manifestação", readonly=True,
                             selection=[
                                 ('pending', 'Pendente'),
                                 ('ciente', 'Ciente da operação'),
                                 ('confirmado', 'Confirmada operação'),
                                 ('desconhecido', 'Desconhecimento'),
                                 ('nao_realizado', 'Não realizado')
                             ])
    formInclusao = fields.Char(string="Forma de Inclusão", readonly=True)
    dataInclusao = fields.Datetime(string="Data de Inclusão", readonly=True)

    @api.one
    @api.constrains('CNPJ', 'partner_id')
    def _check_partner_id(self):
        if self.partner_id and self.CNPJ != self.partner_id.cnpj_cpf:
            raise ValidationError(
                "O Parceiro não possui o mesmo CNPJ/CPF do manifesto atual")

    def _needaction_domain_get(self):
        return [('state', '=', 'pending')]

    def _create_event(self, response, nfe_result, type_event='13'):
        return {
            'type': type_event, 'response': response,
            'company_id': self.company_id.id,
            'status': nfe_result['code'], 'message': nfe_result['message'],
            'create_date': datetime.now(), 'write_date': datetime.now(),
            'end_date': datetime.now(), 'state': 'done',
            'origin': response, 'mde_event_id': self.id
        }

    def _create_attachment(self, event, result):
        file_name = 'evento-manifesto-%s.xml' % datetime.now().strftime('%Y-%m-%d-%H-%M')
        self.env['ir.attachment'].create(
            {
                'name': file_name,
                'datas': base64.b64encode(result['file_returned']),
                'datas_fname': file_name,
                'description': u'Evento Manifesto Destinatário',
                'res_model': 'l10n_br_account.document_event',
                'res_id': event.id
            })

    @api.one
    def action_known_emission(self):
        validate_nfe_configuration(self.company_id)
        nfe_result = send_event(
            self.company_id, self.chNFe, 'ciencia_operacao')
        env_events = self.env['l10n_br_account.document_event']

        event = self._create_event('Ciência da operação', nfe_result)

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
        validate_nfe_configuration(self.company_id)
        nfe_result = send_event(
            self.company_id,
            self.chNFe,
            'confirma_operacao')
        env_events = self.env['l10n_br_account.document_event']

        event = self._create_event('Confirmação da operação', nfe_result)

        if nfe_result['code'] == '135':
            self.state = 'confirmado'
        else:
            event['response'] = 'Confirmação da operação sem êxito'

        event = env_events.create(event)
        self._create_attachment(event, nfe_result)
        return True

    @api.one
    def action_unknown_operation(self):
        validate_nfe_configuration(self.company_id)
        nfe_result = send_event(
            self.company_id,
            self.chNFe,
            'desconhece_operacao')
        env_events = self.env['l10n_br_account.document_event']

        event = self._create_event('Desconhecimento da operação', nfe_result)

        if nfe_result['code'] == '135':
            self.state = 'desconhecido'
        else:
            event['response'] = 'Desconhecimento da operação sem êxito'

        event = env_events.create(event)
        self._create_attachment(event, nfe_result)
        return True

    @api.one
    def action_not_operation(self):
        validate_nfe_configuration(self.company_id)
        nfe_result = send_event(
            self.company_id,
            self.chNFe,
            'nao_realizar_operacao')
        env_events = self.env['l10n_br_account.document_event']

        event = self._create_event('Operação não realizada', nfe_result)

        if nfe_result['code'] == '135':
            self.state = 'nap_realizado'
        else:
            event['response'] = 'Tentativa de Operação não realizada sem êxito'

        event = env_events.create(event)
        self._create_attachment(event, nfe_result)
        return True

    @api.one
    def action_download_xml(self):
        validate_nfe_configuration(self.company_id)
        nfe_result = download_nfe(self.company_id, [self.chNFe])
        env_events = self.env['l10n_br_account.document_event']

        if nfe_result['code'] == '140':
            event = self._create_event('Download NFe concluido', nfe_result,
                                       type_event='10')
            env_events.create(event)
            file_name = 'NFe%s.xml' % self.chNFe
            self.env['ir.attachment'].create(
                {
                    'name': file_name,
                    'datas': base64.b64encode(nfe_result['file_returned']),
                    'datas_fname': file_name,
                    'description': u'XML NFe - Download manifesto do destinatário',
                    'res_model': 'nfe.mde',
                    'res_id': self.id
                })

        else:
            event = self._create_event('Download NFe não efetuado', nfe_result,
                                       type_event='10')
            event = env_events.create(event)
            self._create_attachment(event, nfe_result)
        return True
