# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro <danimaribeiro@gmail.com>, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import re
import pytz
import time
import base64
import logging
from datetime import datetime
from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools.safe_eval import safe_eval
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DTFT

_logger = logging.getLogger(__name__)

try:
    from pytrustnfe.nfse.ginfes import xml_recepcionar_lote_rps
    from pytrustnfe.nfse.ginfes import recepcionar_lote_rps
    from pytrustnfe.nfse.ginfes import consultar_situacao_lote
    from pytrustnfe.nfse.ginfes import consultar_lote_rps
    from pytrustnfe.nfse.ginfes import cancelar_nfse
    from pytrustnfe.certificado import Certificado
except ImportError:
    _logger.error('Cannot import pytrustnfe', exc_info=True)


STATE = {'edit': [('readonly', False)]}


class InvoiceEletronicItem(models.Model):
    _inherit = 'invoice.eletronic.item'

    codigo_tributacao_municipio = fields.Char(
        string=u"Cód. Tribut. Munic.", size=20, readonly=True,
        help="Código de Tributação no Munípio", states=STATE)


class InvoiceEletronic(models.Model):
    _inherit = 'invoice.eletronic'

    state = fields.Selection(
        selection_add=[('waiting', 'Esperando processamento')])

    def _get_state_to_send(self):
        res = super(InvoiceEletronic, self)._get_state_to_send()
        return res + ('waiting',)

    @api.depends('valor_retencao_pis', 'valor_retencao_cofins',
                 'valor_retencao_irrf', 'valor_retencao_inss',
                 'valor_retencao_csll')
    def _compute_total_retencoes(self):
        for item in self:
            total = item.valor_retencao_pis + item.valor_retencao_cofins + \
                item.valor_retencao_irrf + item.valor_retencao_inss + \
                item.valor_retencao_csll
            item.retencoes_federais = total

    retencoes_federais = fields.Monetary(
        string="Retenções Federais", compute=_compute_total_retencoes)

    @api.multi
    def _hook_validation(self):
        errors = super(InvoiceEletronic, self)._hook_validation()
        if self.model == '002':
            issqn_codigo = ''
            if not self.company_id.inscr_mun:
                errors.append(u'Inscrição municipal obrigatória')
            if not self.company_id.cnae_main_id.code:
                errors.append(u'CNAE Principal da empresa obrigatório')
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
                    if not eletr.codigo_tributacao_municipio:
                        errors.append(u'%s - %s - Código de tributação do município \
                        obrigatório' % (
                            eletr.product_id.name,
                            eletr.product_id.service_type_id.name))

        return errors

    @api.multi
    def _prepare_eletronic_invoice_values(self):
        res = super(InvoiceEletronic, self)._prepare_eletronic_invoice_values()
        if self.model != '002':
            return res

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
            'razao_social': partner.legal_name or partner.name,
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
            codigo_servico = re.sub('[^0-9]', '', item.issqn_codigo)

        rps = {
            'numero': self.numero,
            'serie': self.serie.code or '',
            'tipo_rps': '1',
            'data_emissao': dt_emissao,
            'natureza_operacao': '1',  # Tributada no municipio
            'regime_tributacao': '2',  # Estimativa
            'optante_simples':  # 1 - Sim, 2 - Não
            '2' if self.company_id.fiscal_type == '3' else '1',
            'incentivador_cultural': '2',  # 2 - Não
            'status': '1',  # 1 - Normal
            'valor_servico': str("%.2f" % self.valor_final),
            'valor_deducao': '0',
            'valor_pis': str("%.2f" % self.valor_retencao_pis),
            'valor_cofins': str("%.2f" % self.valor_retencao_cofins),
            'valor_inss': str("%.2f" % self.valor_retencao_inss),
            'valor_ir': str("%.2f" % self.valor_retencao_irrf),
            'valor_csll': str("%.2f" % self.valor_retencao_csll),
            'iss_retido': '1' if self.valor_retencao_issqn > 0 else '2',
            'valor_iss':  str("%.2f" % self.valor_issqn),
            'valor_iss_retido': str("%.2f" % self.valor_retencao_issqn),
            'base_calculo': str("%.2f" % self.valor_final),
            'aliquota_issqn': str("%.4f" % (
                self.eletronic_item_ids[0].issqn_aliquota / 100)),
            'valor_liquido_nfse': str("%.2f" % self.valor_final),
            'codigo_servico': int(codigo_servico),
            'codigo_tributacao_municipio':
            self.eletronic_item_ids[0].codigo_tributacao_municipio,
            # '01.07.00 / 00010700',
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
        }

        res.update(nfse_vals)
        return res

    @api.multi
    def action_post_validate(self):
        super(InvoiceEletronic, self).action_post_validate()
        if self.model not in ('002'):
            return

        cert = self.company_id.with_context(
            {'bin_size': False}).nfe_a1_file
        cert_pfx = base64.decodestring(cert)

        certificado = Certificado(
            cert_pfx, self.company_id.nfe_a1_password)

        nfse_values = self._prepare_eletronic_invoice_values()
        xml_enviar = xml_recepcionar_lote_rps(certificado, nfse=nfse_values)

        self.xml_to_send = base64.encodestring(xml_enviar.encode('utf-8'))
        self.xml_to_send_name = 'nfse-enviar-%s.xml' % self.numero

    def _find_attachment_ids_email(self):
        atts = super(InvoiceEletronic, self)._find_attachment_ids_email()
        if self.model not in ('002'):
            return atts

        attachment_obj = self.env['ir.attachment']
        danfe_report = self.env['ir.actions.report'].search(
            [('report_name', '=',
              'br_nfse_ginfes.main_template_br_nfse_danfe_ginfes')])
        report_service = danfe_report.xml_id
        report_name = safe_eval(danfe_report.print_report_name,
                                {'object': self, 'time': time})
        danfse, dummy = self.env.ref(report_service).render_qweb_pdf([self.id])
        filename = "%s.%s" % (report_name, "pdf")
        if danfse:
            danfe_id = attachment_obj.create(dict(
                name=filename,
                datas_fname=filename,
                datas=base64.b64encode(danfse),
                mimetype='application/pdf',
                res_model='account.invoice',
                res_id=self.invoice_id.id,
            ))
            atts.append(danfe_id.id)
        return atts

    @api.multi
    def action_send_eletronic_invoice(self):
        super(InvoiceEletronic, self).action_send_eletronic_invoice()
        if self.model != '002' or self.state in ('done', 'cancel'):
            return
        self.state = 'error'

        cert = self.company_id.with_context(
            {'bin_size': False}).nfe_a1_file
        cert_pfx = base64.decodestring(cert)

        certificado = Certificado(
            cert_pfx, self.company_id.nfe_a1_password)

        consulta_lote = None
        recebe_lote = None

        # Envia o lote apenas se não existir protocolo
        if not self.recibo_nfe:
            xml_to_send = base64.decodestring(self.xml_to_send)
            recebe_lote = recepcionar_lote_rps(
                certificado, xml=xml_to_send, ambiente=self.ambiente)

            retorno = recebe_lote['object']
            if "NumeroLote" in dir(retorno):
                self.recibo_nfe = retorno.Protocolo
                # Espera alguns segundos antes de consultar
                time.sleep(5)
            else:
                mensagem_retorno = retorno.ListaMensagemRetorno\
                    .MensagemRetorno
                self.codigo_retorno = mensagem_retorno.Codigo
                self.mensagem_retorno = mensagem_retorno.Mensagem
                self._create_attachment(
                    'nfse-ret', self,
                    recebe_lote['received_xml'].decode('utf-8'))
                return
        # Monta a consulta de situação do lote
        # 1 - Não Recebido
        # 2 - Não processado
        # 3 - Processado com erro
        # 4 - Processado com sucesso
        obj = {
            'cnpj_prestador': re.sub(
                '[^0-9]', '', self.company_id.cnpj_cpf),
            'inscricao_municipal': re.sub(
                '[^0-9]', '', self.company_id.inscr_mun),
            'protocolo': self.recibo_nfe,
        }
        consulta_situacao = consultar_situacao_lote(
            certificado, consulta=obj, ambiente=self.ambiente)
        ret_rec = consulta_situacao['object']

        if "Situacao" in dir(ret_rec):
            if ret_rec.Situacao in (3, 4):

                consulta_lote = consultar_lote_rps(
                    certificado, consulta=obj, ambiente=self.ambiente)
                retLote = consulta_lote['object']

                if "ListaNfse" in dir(retLote):
                    self.state = 'done'
                    self.codigo_retorno = '100'
                    self.mensagem_retorno = 'NFSe emitida com sucesso'
                    self.verify_code = retLote.ListaNfse.CompNfse \
                        .Nfse.InfNfse.CodigoVerificacao
                    self.numero_nfse = \
                        retLote.ListaNfse.CompNfse.Nfse.InfNfse.Numero
                else:
                    mensagem_retorno = retLote.ListaMensagemRetorno \
                        .MensagemRetorno
                    self.codigo_retorno = mensagem_retorno.Codigo
                    self.mensagem_retorno = mensagem_retorno.Mensagem

            elif ret_rec.Situacao == 1:  # Reenviar caso não recebido
                self.codigo_retorno = ''
                self.mensagem_retorno = 'Aguardando envio'
                self.state = 'draft'
            else:
                self.state = 'waiting'
                self.codigo_retorno = '2'
                self.mensagem_retorno = 'Lote aguardando processamento'
        else:
            self.codigo_retorno = \
                ret_rec.ListaMensagemRetorno.MensagemRetorno.Codigo
            self.mensagem_retorno = \
                ret_rec.ListaMensagemRetorno.MensagemRetorno.Mensagem

        self.env['invoice.eletronic.event'].create({
            'code': self.codigo_retorno,
            'name': self.mensagem_retorno,
            'invoice_eletronic_id': self.id,
        })
        if recebe_lote:
            self._create_attachment(
                'nfse-ret', self,
                recebe_lote['received_xml'])
        if consulta_lote:
            self._create_attachment(
                'rec', self, consulta_lote['sent_xml'])
            self._create_attachment(
                'rec-ret', self,
                consulta_lote['received_xml'])

    @api.multi
    def action_cancel_document(self, context=None, justificativa=None):
        if self.model not in ('002'):
            return super(InvoiceEletronic, self).action_cancel_document(
                justificativa=justificativa)

        cert = self.company_id.with_context(
            {'bin_size': False}).nfe_a1_file
        cert_pfx = base64.decodestring(cert)

        certificado = Certificado(
            cert_pfx, self.company_id.nfe_a1_password)

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
            certificado, cancelamento=canc, ambiente=self.ambiente)
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
