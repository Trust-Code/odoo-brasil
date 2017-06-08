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
                if not company.cert_state == 'valid':
                    continue

                nfe_result = distribuicao_nfe(company, company.last_nsu_nfe)

                if nfe_result['code'] in (138, ):

                    env_mde = self.env['nfe.mde']

                    for nfe in nfe_result['list_nfe']:
                        if nfe['schema'] == 'resNFe_v1.00.xsd':
                            root = objectify.fromstring(nfe['xml'])
                            cnpj_forn = self._mask_cnpj(('%014d' % root.CNPJ))

                            partner = self.env['res.partner'].search(
                                [('cnpj_cpf', '=', cnpj_forn)])

                            total = env_mde.search_count(
                                [('chave_nfe', '=', root.chNFe)])
                            if total > 0:
                                continue

                            manifesto = {
                                'chave_nfe': root.chNFe,
                                'numero_nfe': str(root.chNFe)[25:34],
                                'numero_sequencial': nfe['NSU'],
                                'razao_social': root.xNome,
                                'tipo_operacao': str(root.tpNF),
                                'valor_nfe': root.vNF,
                                'situacao_nfe': str(root.cSitNFe),
                                'state': 'pending',
                                'data_nclusao': datetime.now(),
                                'cnpj_fornecedor': cnpj_forn,
                                'inscricao_estadual': root.IE,
                                'partner_id': partner.id,
                                'data_emissao': datetime.strptime(
                                    str(root.dhEmi)[:19], '%Y-%m-%dT%H:%M:%S'),
                                'company_id': company.id,
                                'forma_inclusao': u'Verificação agendada'
                            }

                            obj_nfe = env_mde.create(manifesto)
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
                    message = "%s - %s" % (nfe_result['code'],
                                           nfe_result['message'])
                    _logger.error(message)
                    if raise_error:
                        raise UserError(message)

            except UserError:
                raise
            except Exception:
                _logger.error("Erro ao consultar Manifesto", exc_info=True)
                if raise_error:
                    raise UserError(
                        u'Não foi possivel efetuar a consulta!\nCheque o log')

    @api.one
    def execute_download(self):
        self.schedule_download(raise_error=True)

    @api.model
    def cron_manifest_automation(self):
        companies = self.env['res.company'].search([])
        for company in companies:
            if company.manifest_automation == 'nenhuma':
                continue

            manifestos = self.env['nfe.mde'].search(
                [('company_id', '=', company.id),
                 ('state', '=', 'pending')], limit=5)
            for manifesto in manifestos:
                manifesto.action_known_emission()
                manifesto.action_download_xml()
