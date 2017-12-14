# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro <danimaribeiro@gmail.com>, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import re
import pytz
import base64
import logging
import hashlib
from datetime import datetime, time
from odoo import api, models
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DTFT

_logger = logging.getLogger(__name__)

try:
    from pytrustnfe.nfse.campinas import cancelar
    from pytrustnfe.nfse.campinas import enviar
    from pytrustnfe.nfse.campinas import consultar_lote_rps
    from pytrustnfe.nfse.campinas import consulta_lote
    from pytrustnfe.certificado import Certificado
except ImportError:
    _logger.debug('Cannot import pytrustnfe')


STATE = {'edit': [('readonly', False)]}


class InvoiceEletronic(models.Model):
    _inherit = 'invoice.eletronic'

    @api.multi
    def _prepare_eletronic_invoice_values(self):
        res = super(InvoiceEletronic, self)._prepare_eletronic_invoice_values()
        if self.model == '011':
            tz = pytz.timezone(self.env.user.partner_id.tz) or pytz.utc
            dt_emissao = datetime.strptime(self.data_emissao, DTFT)
            dt_emissao = pytz.utc.localize(dt_emissao).astimezone(tz)
            dt_emissao = dt_emissao.strftime('%Y-%m-%dT%H:%M:%S')

            partner = self.commercial_partner_id
            city_tomador = partner.city_id
            tomador = {
                'cpf_cnpj': re.sub('[^0-9]', '',
                                   partner.cnpj_cpf or ''),
                'razao_social': partner.legal_name or '',
                'logradouro': partner.street or '',
                'numero': partner.number or '',
                'complemento': partner.street2 or '',
                'bairro': partner.district or 'Sem Bairro',
                'cidade': '%s%s' % (city_tomador.state_id.ibge_code,
                                    city_tomador.ibge_code),
                'cidade_descricao': partner.name or '',
                'uf': partner.state_id.code,
                'cep': re.sub('[^0-9]', '', partner.zip),
                'tipo_logradouro': 'Rua',
                'tipo_bairro': 'Normal',
                'telefone': re.sub('[^0-9]', '', partner.phone.split(' ')[1]),
                'inscricao_municipal': re.sub(
                    '[^0-9]', '', partner.inscr_mun or ''),
                'email': self.partner_id.email or partner.email or '',
            }

            phone = self.company_id.partner_id.phone
            city_prestador = self.company_id.partner_id.city_id
            prestador = {
                'cnpj': re.sub(
                    '[^0-9]', '', self.company_id.partner_id.cnpj_cpf or ''),
                'razao_social': self.company_id.partner_id.legal_name or '',
                'inscricao_municipal': re.sub(
                    '[^0-9]', '', self.company_id.partner_id.inscr_mun or ''),
                'cidade': '%s%s' % (city_prestador.state_id.ibge_code,
                                    city_prestador.ibge_code),
                'tipo_logradouro': 'Rua',
                'cnae': re.sub('[^0-9]', '',
                               self.company_id.cnae_main_id.code or ''),
                'ddd': re.sub('[^0-9]', '', phone.split(' ')[0]),
                'telefone': re.sub('[^0-9]', '', phone.split(' ')[1]),
                'email': self.company_id.partner_id.email or '',
            }

            aliquota_pis = 0.0
            aliquota_cofins = 0.0
            aliquota_csll = 0.0
            aliquota_inss = 0.0
            aliquota_ir = 0.0
            aliquota_issqn = 0.0
            deducoes = []
            itens = []
            for inv_line in self.eletronic_item_ids:
                item = {
                    'descricao': inv_line.product_id.name_template[:80] or '',
                    'quantidade': str("%.0f" % inv_line.quantity),
                    'valor_unitario': str("%.2f" % (inv_line.price_unit)),
                    'valor_total': str(
                        "%.2f" % (inv_line.quantity * inv_line.price_unit)),
                }
                itens.append(item)
                aliquota_pis = inv_line.pis_aliquota
                aliquota_cofins = inv_line.cofins_aliquota
                aliquota_csll = inv_line.csll_aliquota
                aliquota_inss = inv_line.inss_aliquota
                aliquota_ir = inv_line.ir_aliquota
                aliquota_issqn = inv_line.issqn_aliquota

            valor_servico = self.amount_total
            valor_deducao = 0.0
            codigo_atividade = re.sub('[^0-9]', '', self.cnae_id.code or '')
            tipo_recolhimento = self.operation

            data_envio = datetime.strptime(
                self.date_in_out, DTFT)
            data_envio = data_envio.strftime('%Y%m%d')
            assinatura = '%011dNF   %012d%s%s %s%s%015d%015d%010d%014d' % \
                (int(prestador['inscricao_municipal']),
                 int(self.number),
                 data_envio, self.taxation, 'N',
                 'N' if tipo_recolhimento == 'A' else 'S',
                 round(valor_servico * 100),
                 round(valor_deducao * 100),
                 int(codigo_atividade),
                 int(tomador['cpf_cnpj']))

            assinatura = hashlib.sha1(assinatura).hexdigest()

            rps = [{
                'assinatura': assinatura,
                'tomador': tomador,
                'prestador': prestador,
                'serie': self.serie_documento,
                'numero': self.number or '',
                'data_emissao': self.date_emissao,
                'situacao': 'N',
                'serie_prestacao': self.serie.code,
                'codigo_atividade': codigo_atividade,
                'aliquota_atividade': str("%.4f" % aliquota_issqn),
                'tipo_recolhimento': tipo_recolhimento,
                'municipio_prestacao': city_prestador.code,
                'municipio_descricao_prestacao': city_prestador.name or '',
                'operacao': self.operation,
                # 'tributacao': self.taxation,
                'valor_pis': str("%.2f" % self.valor_pis),
                'valor_cofins': str("%.2f" % self.valor_cofins),
                'valor_csll': str("%.2f" % self.valor_csll),
                'valor_inss': str("%.2f" % self.valor_inss),
                'valor_ir': str("%.2f" % self.valor_ir),
                'aliquota_pis': str("%.2f" % aliquota_pis),
                'aliquota_cofins': str("%.2f" % aliquota_cofins),
                'aliquota_csll': str("%.2f" % aliquota_csll),
                'aliquota_inss': str("%.2f" % aliquota_inss),
                'aliquota_ir': str("%.2f" % aliquota_ir),
                'descricao': "%s" % (self.fiscal),
                'deducoes': deducoes,
                'itens': itens,
            }]

            nfse_vals = {
                'cidade': '6291',
                'cpf_cnpj': prestador['cnpj'],
                'remetente': prestador['razao_social'],
                'transacao': '',
                'data_inicio': data_envio,
                'data_fim': data_envio,
                'total_rps': '1',
                'total_servicos': str("%.2f" % self.amount_total),
                'total_deducoes': '0',
                'lote_id': '%s' % self.lote_nfse,
                'lista_rps': rps
            }
            res.update(nfse_vals)
        return res

    def _find_attachment_ids_email(self):
        atts = super(InvoiceEletronic, self)._find_attachment_ids_email()
        if self.model not in ('011'):
            return atts

        attachment_obj = self.env['ir.attachment']
        danfe_report = self.env['ir.actions.report.xml'].search(
            [('report_name', '=',
              'br_nfse.main_template_br_nfse_danfe_ginfes')])
        report_service = danfe_report.report_name
        danfse = self.env['report'].get_pdf([self.id], report_service)
        if danfse:
            danfe_id = attachment_obj.create(dict(
                name="ginfes-%08d.pdf" % int(self.numero_nfse),
                datas_fname="ginfes-%08d.pdf" % int(self.numero_nfse),
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
        if self.model == '011' and self.state not in ('done', 'cancel'):
            self.state = 'error'

            cert = self.company_id.with_context(
                {'bin_size': False}).nfe_a1_file
            cert_pfx = base64.decodestring(cert)

            certificado = Certificado(
                cert_pfx, self.company_id.nfe_a1_password)

            # consulta_lote = None
            recebe_lote = None

            # Envia o lote apenas se não existir protocolo
            if not self.recibo_nfe:
                xml_to_send = base64.decodestring(self.xml_to_send)
                recebe_lote = enviar(
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
                        'nfse-ret', self, recebe_lote['received_xml'])
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
            consulta_situacao = consulta_lote(
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
                    'nfse-ret', self, recebe_lote['received_xml'])
            if consulta_lote:
                self._create_attachment(
                    'rec', self, consulta_lote['sent_xml'])
                self._create_attachment(
                    'rec-ret', self, consulta_lote['received_xml'])

    @api.multi
    def action_cancel_document(self, context=None, justificativa=None):
        if self.model not in ('011'):
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
        cancel = cancelar(
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
