# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro <danimaribeiro@gmail.com>, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import re
import pytz
import base64
import logging
from datetime import datetime
from odoo import api, fields, models
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DTFT

_logger = logging.getLogger(__name__)

try:
    from pytrustnfe.nfse.simpliss import xml_recepcionar_lote_rps
    from pytrustnfe.nfse.simpliss import recepcionar_lote_rps
    from pytrustnfe.nfse.simpliss import consultar_situacao_lote
    from pytrustnfe.nfse.simpliss import cancelar_nfse
    from pytrustnfe.certificado import Certificado
except ImportError:
    _logger.debug('Cannot import pytrustnfe')


STATE = {'edit': [('readonly', False)]}


class InvoiceEletronicItem(models.Model):
    _inherit = 'invoice.eletronic.item'

    codigo_servico_paulistana = fields.Char(
        string='Código NFSe Paulistana', size=5, readonly=True, states=STATE)


class InvoiceEletronic(models.Model):
    _inherit = 'invoice.eletronic'

    @api.multi
    def _hook_validation(self):
        errors = super(InvoiceEletronic, self)._hook_validation()
        if self.model == '008':
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
        if self.model == '008':
            tz = pytz.timezone(self.env.user.partner_id.tz) or pytz.utc
            dt_emissao = datetime.strptime(self.data_emissao, DTFT)
            dt_emissao = pytz.utc.localize(dt_emissao).astimezone(tz)
            dt_emissao = dt_emissao.strftime('%Y-%m-%dT%H:%M:%S')

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
            prestador = {
                'cnpj': re.sub(
                    '[^0-9]', '', self.company_id.partner_id.cnpj_cpf or ''),
                'inscricao_municipal': re.sub(
                    '[^0-9]', '', self.company_id.partner_id.inscr_mun or ''),
                'cidade': '%s%s' % (city_prestador.state_id.ibge_code,
                                    city_prestador.ibge_code),
                'cnae': re.sub('[^0-9]', '', self.company_id.cnae_main_id.code)
            }

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
                'natureza_operacao': '1',  # Tributada no municipio
                'regime_tributacao': '7',  # Estimativa
                'optante_simples':  # 1 - Sim, 2 - Não
                '2' if self.company_id.fiscal_type == '3' else '1',
                'incentivador_cultural': '2',  # 2 - Não
                'status': '1',  # 1 - Normal
                'valor_servico': str("%.2f" % self.valor_final),
                'valor_deducao': '0',
                'valor_pis': str("%.2f" % self.valor_pis),
                'valor_cofins': str("%.2f" % self.valor_cofins),
                'valor_inss': str("%.2f" % 0.0),
                'valor_ir': str("%.2f" % 0.0),
                'valor_csll': str("%.2f" % 0.0),
                'iss_retido': '1' if self.valor_retencao_issqn > 0 else '2',
                'valor_iss': str("%.2f" % self.valor_issqn),
                'valor_iss_retido': str("%.2f" % self.valor_retencao_issqn),
                'base_calculo': str("%.2f" % 0.0),
                'aliquota_issqn': str("%.2f" % 0.0),
                'valor_liquido_nfse': str("%.2f" % self.valor_final),
                'codigo_servico': codigo_servico,
                'cnae_servico': prestador['cnae'],
                'codigo_tributacao_municipio': codigo_servico,
                'descricao': descricao,
                'codigo_municipio': prestador['cidade'],
                'itens_servico': itens_servico,
                'tomador': tomador,
                'prestador': prestador,
            }

            nfse_vals = {
                'numero_lote': self.id,
                'inscricao_municipal': prestador['inscricao_municipal'],
                'cnpj_prestador': prestador['cnpj'],
                'lista_rps': [rps],
                'senha': self.company_id.senha_ambiente_nfse
            }

            res.update(nfse_vals)
        return res

    @api.multi
    def action_post_validate(self):
        super(InvoiceEletronic, self).action_post_validate()
        if self.model not in ('008'):
            return

        cert = self.company_id.with_context(
            {'bin_size': False}).nfe_a1_file
        cert_pfx = base64.decodestring(cert)

        certificado = Certificado(
            cert_pfx, self.company_id.nfe_a1_password)

        nfse_values = self._prepare_eletronic_invoice_values()
        xml_enviar = xml_recepcionar_lote_rps(certificado, nfse=nfse_values)

        self.xml_to_send = base64.encodestring(xml_enviar)
        self.xml_to_send_name = 'nfse-enviar-%s.xml' % self.numero

    @api.multi
    def action_send_eletronic_invoice(self):
        super(InvoiceEletronic, self).action_send_eletronic_invoice()
        if self.model == '008':
            self.state = 'error'

            xml_to_send = base64.decodestring(self.xml_to_send)
            resposta = recepcionar_lote_rps(
                None, xml=xml_to_send, ambiente=self.ambiente)

            recibo = None
            retorno = resposta['object']
            retorno = resposta['object'].Body.RecepcionarLoteRpsResponse
            retorno = retorno.getchildren()[0]
            if "NumeroLote" in dir(retorno):
                obj = {
                    'cnpj_prestador': re.sub(
                        '[^0-9]', '', self.company_id.cnpj_cpf),
                    'inscricao_municipal': re.sub(
                        '[^0-9]', '', self.company_id.inscr_mun),
                    'protocolo': retorno.Protocolo,
                    'senha': self.company_id.senha_ambiente_nfse
                }
                self.recibo_nfe = retorno.Protocolo

                import time
                while True:
                    recibo = consultar_situacao_lote(
                        None, consulta=obj, ambiente=self.ambiente)
                    ret_rec = recibo['object'].Body.ConsultarSituacaoLoteRpsResponse.ConsultarSituacaoLoteRpsResult

                    time.sleep(2)
                    if "ListaMensagemRetorno" in dir(ret_rec):
                        self.codigo_retorno = ret_rec.ListaMensagemRetorno.MensagemRetorno.Codigo
                        self.mensagem_retorno = ret_rec.ListaMensagemRetorno.MensagemRetorno.Mensagem
                        break
                    if ret_rec.Situacao in (3, 4):
                        if ret_rec.Situacao == 3:
                            self.state = 'done'
                        break
            else:
                self.codigo_retorno = \
                    retorno.ListaMensagemRetorno.MensagemRetorno.Codigo
                self.mensagem_retorno = \
                    retorno.ListaMensagemRetorno.MensagemRetorno.Mensagem

            self.env['invoice.eletronic.event'].create({
                'code': self.codigo_retorno,
                'name': self.mensagem_retorno,
                'invoice_eletronic_id': self.id,
            })
            self._create_attachment('nfse-ret', self, resposta['received_xml'])
            if recibo:
                self._create_attachment('rec', self, recibo['sent_xml'])
                self._create_attachment(
                    'rec-ret', self, recibo['received_xml'])

    @api.multi
    def action_cancel_document(self, context=None, justificativa=None):
        if self.model not in ('008'):
            return super(InvoiceEletronic, self).action_cancel_document(
                justificativa=justificativa)

        cert = self.company_id.with_context({'bin_size': False}).nfe_a1_file
        cert_pfx = base64.decodestring(cert)
        certificado = Certificado(cert_pfx, self.company_id.nfe_a1_password)

        company = self.company_id
        canc = {
            'cnpj_remetente': re.sub('[^0-9]', '', company.cnpj_cpf),
            'inscricao_municipal': re.sub('[^0-9]', '', company.inscr_mun),
            'numero_nfse': self.numero_nfse,
            'codigo_verificacao': self.verify_code,
            'assinatura': '%s%s' % (
                re.sub('[^0-9]', '', company.inscr_mun),
                self.numero_nfse.zfill(12)
            )
        }
        resposta = cancelar_nfse(certificado, cancelamento=canc)
        retorno = resposta['object']
        if retorno.Cabecalho.Sucesso:
            self.state = 'cancel'
            self.codigo_retorno = '100'
            self.mensagem_retorno = 'Nota Fiscal Paulistana Cancelada'
        else:
            self.codigo_retorno = retorno.Erro.Codigo
            self.mensagem_retorno = retorno.Erro.Descricao

        self.env['invoice.eletronic.event'].create({
            'code': self.codigo_retorno,
            'name': self.mensagem_retorno,
            'invoice_eletronic_id': self.id,
        })
        self._create_attachment('canc', self, resposta['sent_xml'])
        self._create_attachment('canc-ret', self, resposta['received_xml'])
