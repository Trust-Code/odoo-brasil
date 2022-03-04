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
    _description = "Scheduler para efetuar download de notas"

    state = fields.Selection(
        string="Estado",
        selection=[('init', 'Não iniciado'), ('done', 'Finalizado')],
        default='init'
    )

    @staticmethod
    def _mask_cnpj_cpf(cnpj_cpf):
        val = re.sub('[^0-9]', '', cnpj_cpf or '')
        if len(val) == 11:
            return "%s.%s.%s-%s"\
                % (val[0:3], val[3:6], val[6:9], val[9:11])
        else:
            return "%s.%s.%s/%s-%s"\
                    % (val[0:2], val[2:5], val[5:8], val[8:12], val[12:14])

    @api.model
    def schedule_download(self, raise_error=False):
        companies = self.env['res.company'].search([])
        total = 0
        messages = []
        for company in companies:
            try:
                if not company.l10n_br_cert_state == 'valid':
                    continue

                nfe_result = distribuicao_nfe(company, company.last_nsu_nfe)

                message = "%s - %s / %s" % (
                    nfe_result['code'], nfe_result['message'],
                    company.name)
                _logger.warning(message)
                if nfe_result['code'] in (138, ):

                    env_mde = self.env['nfe.mde']
                    for nfe in nfe_result['list_nfe']:
                        if nfe['schema'] == 'resNFe_v1.01.xsd':
                            total += 1
                            root = objectify.fromstring(nfe['xml'])
                            cnpj_cpf = 'CNPJ' in dir(root) and root.CNPJ.text or False
                            if not cnpj_cpf:
                                cnpj_cpf = root.CPF.text
                            cnpj_forn = self._mask_cnpj_cpf(cnpj_cpf)

                            partner = self.env['res.partner'].search(
                                [('l10n_br_cnpj_cpf', '=', cnpj_forn)])

                            total_mde = env_mde.search_count(
                                [('chave_nfe', '=', root.chNFe)])
                            if total_mde > 0:
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
                                'data_inclusao': datetime.now(),
                                'cnpj_fornecedor': cnpj_forn,
                                'inscricao_estadual': root.IE,
                                'partner_id': partner.id,
                                'data_emissao': datetime.strptime(
                                    str(root.dhEmi)[:19], '%Y-%m-%dT%H:%M:%S'),
                                'company_id': company.id,
                                'forma_inclusao': 'Verificação agendada'
                            }

                            obj_nfe = env_mde.create(manifesto)

                            file_name = 'resumo_nfe-%s.xml' % nfe['NSU']
                            self.env['ir.attachment'].create(
                                {
                                    'name': file_name,
                                    'datas': base64.b64encode(nfe['xml']),
                                    'description': u'NFe via manifesto',
                                    'res_model': 'nfe.mde',
                                    'res_id': obj_nfe.id
                                })
                        elif nfe['schema'] in ('procNFe_v3.10.xsd',
                                               'procNFe_v4.00.xsd'):
                            total += 1
                            root = objectify.fromstring(nfe['xml'])
                            infNfe = root.NFe.infNFe
                            protNFe = root.protNFe.infProt
                            if hasattr(infNfe.emit, "CNPJ"):
                                cnpj_forn = self._mask_cnpj_cpf(
                                    ('%014d' % infNfe.emit.CNPJ))
                            else:
                                cnpj_forn = self._mask_cnpj_cpf(
                                    ('%011d' % infNfe.emit.CPF))

                            partner = self.env['res.partner'].search(
                                [('l10n_br_cnpj_cpf', '=', cnpj_forn)])

                            obj_nfe = env_mde.search(
                                [('chave_nfe', '=', protNFe.chNFe)])
                            if obj_nfe:
                                obj_nfe.write({
                                    'state': 'ciente',
                                    'nfe_processada': base64.encodestring(
                                        nfe['xml']),
                                    'nfe_processada_name': "NFe%08d.xml" %
                                    infNfe.ide.nNF,
                                })
                            else:
                                manifesto = {
                                    'chave_nfe': protNFe.chNFe,
                                    'numero_nfe': infNfe.ide.nNF,
                                    'numero_sequencial': nfe['NSU'],
                                    'razao_social': infNfe.emit.xNome,
                                    'tipo_operacao': str(infNfe.ide.tpNF),
                                    'valor_nfe': infNfe.total.ICMSTot.vNF,
                                    'situacao_nfe': '',  # str(root.cSitNFe),
                                    'state': 'ciente',
                                    'data_inclusao': datetime.now(),
                                    'cnpj_fornecedor': cnpj_forn,
                                    'inscricao_estadual': infNfe.emit.IE,
                                    'partner_id': partner.id,
                                    'data_emissao': datetime.strptime(
                                        str(infNfe.ide.dhEmi)[:19],
                                        '%Y-%m-%dT%H:%M:%S'),
                                    'company_id': company.id,
                                    'forma_inclusao': u'Verificação agendada',
                                    'nfe_processada': base64.encodestring(
                                        nfe['xml']),
                                    'nfe_processada_name': "NFe%08d.xml" %\
                                    infNfe.ide.nNF
                                }

                                obj_nfe = env_mde.create(manifesto)

                            file_name = 'resumo_nfe-%s.xml' % nfe['NSU']

                        company.last_nsu_nfe = nfe['NSU']
                elif nfe_result['code'] in (137, ):
                    continue
                else:
                    messages += [message]

                self._cr.commit()
            except UserError:
                raise
            except Exception:
                _logger.error("Erro ao consultar Manifesto", exc_info=True)
                if raise_error:
                    raise UserError(
                        u'Não foi possivel efetuar a consulta!\nCheque o log')
        if raise_error:
            raise UserError('Total de documentos localizados %s\n%s' % (
                total, '\n'.join(messages)))

    def execute_download(self):
        self.schedule_download(raise_error=True)

    @api.model
    def cron_manifest_automation(self):
        companies = self.env['res.company'].search([])
        for company in companies:
            if not company.manifest_automation:
                continue

            manifestos = self.env['nfe.mde'].search(
                [('company_id', '=', company.id),
                 ('is_processed', '=', False)], limit=50)
            for manifesto in manifestos:
                try:
                    if not manifesto.action_known_emission():
                        continue
                    if not manifesto.action_download_xml():
                        continue
                    manifesto.action_import_xml()
                except Exception as e:
                    _logger.error("Erro ao processar manifesto", exc_info=True)
                    manifesto.message_post(
                        body='Não foi possível processar o manifesto \
                        completamente: %s' % e.name)
                finally:
                    manifesto.is_processed = True
                    self._cr.commit()
