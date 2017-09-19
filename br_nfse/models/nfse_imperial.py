# -*- coding: utf-8 -*-
# © 2017 Danimar Ribeiro <danimaribeiro@gmail.com>, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import re
import pytz
import base64
import logging
from datetime import datetime
from odoo import api, models
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DTFT

_logger = logging.getLogger(__name__)

try:
    from pytrustnfe.nfse.imperial import xml_processa_rps
    from pytrustnfe.nfse.imperial import processa_rps
    from pytrustnfe.nfse.imperial import consulta_protocolo
    from pytrustnfe.nfse.imperial import consulta_notas_protocolo
    from pytrustnfe.nfse.imperial import cancelar_nfse
except ImportError:
    _logger.debug('Cannot import pytrustnfe')


STATE = {'edit': [('readonly', False)]}


class InvoiceEletronic(models.Model):
    _inherit = 'invoice.eletronic'

    @api.multi
    def _hook_validation(self):
        errors = super(InvoiceEletronic, self)._hook_validation()
        if self.model == '010':
            issqn_codigo = ''
            if not self.company_id.inscr_mun:
                errors.append(u'Inscrição municipal obrigatória')
            for eletr in self.eletronic_item_ids:
                prod = u"Produto: %s - %s" % (eletr.product_id.default_code,
                                              eletr.product_id.name)
                if eletr.tipo_produto == 'product':
                    errors.append(
                        u'Esse documento permite apenas serviços - %s' % prod)
                if eletr.tipo_produto == 'service':
                    if not eletr.issqn_codigo:
                        errors.append(u'%s - Código de Serviço' % prod)
                    if not issqn_codigo:
                        issqn_codigo = eletr.issqn_codigo
                    if issqn_codigo != eletr.issqn_codigo:
                        errors.append(u'%s - Apenas itens com o mesmo código \
                                      de serviço podem ser enviados' % prod)

        return errors

    @api.multi
    def _prepare_eletronic_invoice_values(self):
        res = super(InvoiceEletronic, self)._prepare_eletronic_invoice_values()
        if self.model == '010':
            tz = pytz.timezone(self.env.user.partner_id.tz) or pytz.utc
            dt_emissao = datetime.strptime(self.data_emissao, DTFT)
            dt_emissao = pytz.utc.localize(dt_emissao).astimezone(tz)

            partner = self.commercial_partner_id
            city_tomador = partner.city_id
            tomador = {
                'tipo_cpfcnpj': 2 if partner.is_company else 1,
                'cnpj_cpf': re.sub('[^0-9]', '',
                                   partner.cnpj_cpf or ''),
                'razao_social': partner.legal_name or '',
                'logradouro': partner.street or '',
                'numero': partner.number or '',
                'complemento': partner.street2 or '',
                'bairro': partner.district or 'Sem Bairro',
                'cidade': '%s%s' % (city_tomador.state_id.ibge_code,
                                    city_tomador.ibge_code),
                'uf': partner.state_id.code,
                'cep': re.sub('[^0-9]', '', partner.zip),
                'telefone': re.sub('[^0-9]', '', partner.phone or ''),
                'inscricao_municipal': re.sub(
                    '[^0-9]', '', partner.inscr_mun or ''),
                'email': self.partner_id.email or partner.email or '',
            }
            city_prestador = self.company_id.partner_id.city_id
            company = self.company_id
            prestador = {
                'cnpj': re.sub(
                    '[^0-9]', '', company.partner_id.cnpj_cpf or ''),
                'inscricao_municipal': re.sub(
                    '[^0-9]', '', company.partner_id.inscr_mun or ''),
                'logradouro': company.street or '',
                'numero': company.number or '',
                'complemento': company.street2 or '',
                'bairro': company.district or 'Sem Bairro',
                'municipio': company.city_id.name,
                'uf': company.state_id.code,
                'cep': re.sub('[^0-9]', '', partner.zip),
            }
            valor_tributos = 0.0
            itens_servico = []
            descricao = ''
            codigo_servico = ''
            for item in self.eletronic_item_ids:
                descricao += item.name + '\n'
                itens_servico.append({
                    'descricao': item.name,
                    'quantidade': str("%.2f" % item.quantidade),
                    'valor_unitario': str("%.2f" % item.preco_unitario)
                })
                codigo_servico = item.issqn_codigo

            rps = {
                'numero': self.numero,
                'serie': self.serie.code or '',
                'tipo_rps': '1',
                'data_emissao': dt_emissao,
                'optante_simples':  # 1 - Sim, 2 - Não
                '2' if self.company_id.fiscal_type == '3' else '1',
                'valor_servico': self.valor_final,
                'valor_deducao': 0.0,
                'valor_pis': self.valor_pis,
                'valor_cofins': self.valor_cofins,
                'valor_inss': self.valor_retencao_inss,
                'valor_ir': self.valor_retencao_irrf,
                'valor_csll': self.valor_retencao_csll,
                'iss_retido': '1' if self.valor_retencao_issqn > 0 else '2',
                'valor_iss': self.valor_issqn,
                'valor_iss_retido': self.valor_retencao_issqn,
                'base_calculo': self.valor_final,
                'aliquota_issqn': self.eletronic_item_ids[0].issqn_aliquota,
                'valor_liquido_nfse': self.valor_final,
                'codigo_servico': codigo_servico,
                'cnae_servico': prestador['cnae'],
                'codigo_tributacao_municipio': codigo_servico,
                'descricao': descricao,
                'codigo_municipio': prestador['cidade'],
                'itens_servico': itens_servico,
                'tomador': tomador,
                'prestador': prestador,
                'impostos': [],
            }

            nfse_vals = {
                'numero_lote': self.id,
                'inscricao_municipal': prestador['inscricao_municipal'],
                'cnpj_prestador': prestador['cnpj'],
                'lista_rps': [rps],
                'valor_tributos': valor_tributos,
                'codigo_usuario': self.company_id.codigo_nfse_usuario,
                'codigo_contribuinte': self.company_id.codigo_nfse_empresa,
            }

            res.update(nfse_vals)
        return res

    @api.multi
    def action_post_validate(self):
        super(InvoiceEletronic, self).action_post_validate()
        if self.model not in ('010'):
            return

        nfse_values = self._prepare_eletronic_invoice_values()
        xml_enviar = xml_processa_rps(None, nfse=nfse_values)

        self.xml_to_send = base64.encodestring(xml_enviar)
        self.xml_to_send_name = 'nfse-enviar-%s.xml' % self.numero

    @api.multi
    def action_send_eletronic_invoice(self):
        super(InvoiceEletronic, self).action_send_eletronic_invoice()
        if self.model == '010' and self.state not in ('done', 'cancel'):
            self.state = 'error'

            recebe_lote = None

            xml_to_send = base64.decodestring(self.xml_to_send)
            recebe_lote = processa_rps(
                None, xml=xml_to_send, ambiente=self.ambiente_nfse)

            retorno = recebe_lote['object'].Body['ws_nfe.PROCESSARPSResponse']
            retorno = retorno['Sdt_processarpsout']

            if retorno.Retorno:
                self.state = 'done'
                self.codigo_retorno = '100'
                self.mensagem_retorno = 'NFSe emitida com sucesso'
                # TODO Ajustar o retorno aqui
                # self.verify_code = retorno.NovaNfse.CodigoVerificacao

            else:
                self.codigo_retorno = -1
                self.mensagem_retorno = retorno.Messages[0].Message.Description

            self.env['invoice.eletronic.event'].create({
                'code': self.codigo_retorno,
                'name': self.mensagem_retorno,
                'invoice_eletronic_id': self.id,
            })
            if recebe_lote:
                self._create_attachment(
                    'nfse-ret', self, recebe_lote['received_xml'])

    @api.multi
    def action_cancel_document(self, context=None, justificativa=None):
        if self.model not in ('010'):
            return super(InvoiceEletronic, self).action_cancel_document(
                justificativa=justificativa)

        company = self.company_id
        city_prestador = self.company_id.partner_id.city_id
        canc = {
            'cnpj_prestador': re.sub('[^0-9]', '', company.cnpj_cpf),
            'inscricao_municipal': re.sub('[^0-9]', '', company.inscr_mun),
            'cidade': '%s%s' % (city_prestador.state_id.ibge_code,
                                city_prestador.ibge_code),
            'numero_nfse': self.numero_nfse,
            'codigo_cancelamento': '1',
            'senha': self.company_id.senha_ambiente_nfse
        }
        cancel = cancelar_nfse(
            None, cancelamento=canc, ambiente=self.ambiente_nfse)
        retorno = cancel['object'].Body.CancelarNfseResponse.CancelarNfseResult
        if "Cancelamento" in dir(retorno):
            self.state = 'cancel'
            self.codigo_retorno = '100'
            self.mensagem_retorno = u'Nota Fiscal de Serviço Cancelada'
        else:
            # E79 - Nota já está cancelada
            if retorno.ListaMensagemRetorno.MensagemRetorno.Codigo != 'E79':
                mensagem = "%s - %s" % (
                    retorno.ListaMensagemRetorno.MensagemRetorno.Codigo,
                    retorno.ListaMensagemRetorno.MensagemRetorno.Mensagem
                )
                raise UserError(mensagem)

            self.state = 'cancel'
            self.codigo_retorno = '100'
            self.mensagem_retorno = u'Nota Fiscal de Serviço Cancelada'

        self.env['invoice.eletronic.event'].create({
            'code': self.codigo_retorno,
            'name': self.mensagem_retorno,
            'invoice_eletronic_id': self.id,
        })
        self._create_attachment('canc', self, cancel['sent_xml'])
        self._create_attachment('canc-ret', self, cancel['received_xml'])
