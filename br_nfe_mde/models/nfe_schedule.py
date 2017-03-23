# -*- coding: utf-8 -*-
# © 2015 Danimar Ribeiro <danimaribeiro@gmail.com>, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import re
import base64
import logging
from lxml import objectify
from datetime import datetime
from ..service.mde import distribuicao_nfe
from odoo import models, api, fields
from odoo.exceptions import UserError


_logger = logging.getLogger(__name__)


class NfeSchedule(models.TransientModel):
    _name = 'nfe.schedule'

    state = fields.Selection(
        string="Estado",
        selection=[('init', 'Não iniciado'), ('done', 'Finalizado')],
        default='init'
    )

    @staticmethod
    def _mask_cnpj(cnpj):
        if cnpj:
            val = re.sub('[^0-9]', '', cnpj)
            if len(val) == 14:
                cnpj = "%s.%s.%s/%s-%s" % (val[0:2], val[2:5], val[5:8],
                                           val[8:12], val[12:14])
        return cnpj

    @api.model
    def schedule_download(self, raise_error=False):
        companies = self.env['res.company'].search([])
        for company in companies:
            try:
                nfe_result = distribuicao_nfe(company, company.last_nsu_nfe)

                if nfe_result['code'] == '137' or nfe_result['code'] == '138':
                    event = {
                        'type': '12', 'company_id': company.id,
                        'response': 'Consulta distribuição: sucesso',
                        'status': nfe_result['code'],
                        'message': nfe_result['message'],
                        'create_date': datetime.now(),
                        'write_date': datetime.now(),
                        'end_date': datetime.now(),
                        'state': 'done', 'origin': 'Scheduler Download'
                    }

                    obj = env_events.create(event)
                    self.env['ir.attachment'].create(
                        {
                            'name': u"Consulta manifesto - {0}".format(
                                company.cnpj_cpf),
                            'datas': base64.b64encode(
                                nfe_result['file_returned']),
                            'datas_fname': u"Consulta manifesto - {0}".format(
                                company.cnpj_cpf),
                            'description': u'Consulta distribuição: sucesso',
                            'res_model': 'l10n_br_account.document_event',
                            'res_id': obj.id
                        })

                    env_mde = self.env['nfe.mde']

                    for nfe in nfe_result['list_nfe']:
                        if nfe['schema'] == 'resNFe_v1.00.xsd':
                            root = objectify.fromstring(nfe['xml'])
                            cnpj_forn = self._mask_cnpj(('%014d' % root.CNPJ))

                            partner = self.env['res.partner'].search(
                                [('cnpj_cpf', '=', cnpj_forn)])

                            invoice_eletronic = {
                                'chNFe': root.chNFe,
                                'nSeqEvento': nfe['NSU'], 'xNome': root.xNome,
                                'tpNF': str(root.tpNF), 'vNF': root.vNF,
                                'cSitNFe': str(root.cSitNFe),
                                'state': 'pending',
                                'dataInclusao': datetime.now(),
                                'CNPJ': cnpj_forn,
                                'IE': root.IE,
                                'partner_id': partner.id,
                                'dEmi': datetime.strptime(str(root.dhEmi)[:19],
                                                          '%Y-%m-%dT%H:%M:%S'),
                                'company_id': company.id,
                                'formInclusao': u'Verificação agendada'
                            }

                            obj_nfe = env_mde.create(invoice_eletronic)
                            file_name = 'resumo_nfe-%s.xml' % nfe['NSU']
                            self.env['ir.attachment'].create(
                                {
                                    'name': file_name,
                                    'datas': base64.b64encode(nfe['xml']),
                                    'datas_fname': file_name,
                                    'description': u'NFe via manifesto',
                                    'res_model': 'nfe.mde',
                                    'res_id': obj_nfe.id
                                })

                        company.last_nsu_nfe = nfe['NSU']
                else:

                    event = {
                        'type': '12',
                        'response': 'Consulta distribuição com problemas',
                        'company_id': company.id,
                        'file_returned': nfe_result['file_returned'],
                        'file_sent': nfe_result['file_sent'],
                        'message': nfe_result['message'],
                        'create_date': datetime.now(),
                        'write_date': datetime.now(),
                        'end_date': datetime.now(),
                        'status': nfe_result['code'],
                        'state': 'done', 'origin': 'Scheduler Download'
                    }

                    obj = env_events.create(event)
                    self.env['ir.attachment'].create(
                        {
                            'name': u"Consulta manifesto - {0}".format(
                                company.cnpj_cpf),
                            'datas': base64.b64encode(
                                nfe_result['file_returned']),
                            'datas_fname': u"Consulta manifesto - {0}".format(
                                company.cnpj_cpf),
                            'description': u'Consulta manifesto com erro',
                            'res_model': 'l10n_br_account.document_event',
                            'res_id': obj.id
                        })

            except Exception:
                _logger.error("Erro ao consultar Manifesto", exc_info=True)
                if raise_error:
                    raise UserError(
                        u'Não foi possivel efetuar a consulta!\nCheque o log')

    @api.one
    def execute_download(self):
        self.schedule_download(raise_error=True)
