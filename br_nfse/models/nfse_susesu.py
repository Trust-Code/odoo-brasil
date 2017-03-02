# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro <danimaribeiro@gmail.com>, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import re
import pytz
import base64
import logging
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DTFT

_logger = logging.getLogger(__name__)

try:
    from pytrustnfe.nfse.susesu import xml_enviar_nota_retorna_url
    from pytrustnfe.nfse.susesu import enviar_nota_retorna_url
except ImportError:
    _logger.debug('Cannot import pytrustnfe')


class InvoiceEletronic(models.Model):
    _inherit = 'invoice.eletronic'

    url_danfe = fields.Char(
        string=u'Url de Impressão Danfe', size=500, readonly=True)

    @api.multi
    def _hook_validation(self):
        errors = super(InvoiceEletronic, self)._hook_validation()
        if self.model == '009':
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
        if self.model == '009':
            tz = pytz.timezone(self.env.user.partner_id.tz) or pytz.utc
            dt_emissao = datetime.strptime(self.data_emissao, DTFT)
            dt_emissao = pytz.utc.localize(dt_emissao).astimezone(tz)
            dt_emissao = dt_emissao.strftime('%Y-%m-%d')

            partner = self.commercial_partner_id
            city_tomador = partner.city_id
            tomador = {
                'cpf_cnpj': re.sub('[^0-9]', '',
                                   partner.cnpj_cpf or ''),
                'razao_social': partner.legal_name or '',
                'logradouro': "%s, %s" % (partner.street, partner.number),
                'bairro': partner.district or 'Sem Bairro',
                'cidade': '%s%s' % (city_tomador.state_id.ibge_code,
                                    city_tomador.ibge_code),
                'uf': partner.state_id.code,
                'cep': re.sub('[^0-9]', '', partner.zip),
                'telefone': re.sub('[^0-9]', '', partner.phone or ''),
                'inscricao_municipal': re.sub(
                    '[^0-9]', '', partner.inscr_mun or ''),
                'inscricao_estadual': re.sub(
                    '[^0-9]', '', partner.inscr_est or ''),
                'email': self.partner_id.email or partner.email or '',
            }
            city_prestador = self.company_id.partner_id.city_id
            prestador = {
                'cnpj': re.sub(
                    '[^0-9]', '', self.company_id.partner_id.cnpj_cpf or ''),
                'cidade': '%s%s' % (city_prestador.state_id.ibge_code,
                                    city_prestador.ibge_code),
                'cidade_descricao': city_prestador.name or '',
            }

            descricao = ''
            codigo_servico = ''
            for item in self.eletronic_item_ids:
                descricao += item.name + '\n'
                codigo_servico = item.issqn_codigo

            nfse_vals = {
                'codigo_prefeitura': '3150',
                'senha_nfd': 'fiscalb',
                'tomador': tomador,
                'prestador': prestador,
                'cnpj_prestador': prestador['cnpj'],
                'total_servicos': str("%.2f" % self.valor_final),
                'numero': self.numero,
                'data_emissao': dt_emissao,
                'aliquota_atividade': '0.000',
                'codigo_atividade': codigo_servico,
                'valor_pis': str("%.2f" % self.valor_pis),
                'valor_cofins': str("%.2f" % self.valor_cofins),
                'valor_csll': str("%.2f" % 0.0),
                'valor_inss': str("%.2f" % 0.0),
                'valor_ir': str("%.2f" % 0.0),
                'aliquota_pis': str("%.2f" % 0.0),
                'aliquota_cofins': str("%.2f" % 0.0),
                'aliquota_csll': str("%.2f" % 0.0),
                'aliquota_inss': str("%.2f" % 0.0),
                'aliquota_ir': str("%.2f" % 0.0),
                'valor_deducao': '0',
                'descricao': descricao,
                'observacoes': self.informacoes_complementares,
            }

            res.update(nfse_vals)
        return res

    @api.multi
    def action_post_validate(self):
        super(InvoiceEletronic, self).action_post_validate()
        if self.model not in ('009'):
            return

        nfse_values = self._prepare_eletronic_invoice_values()
        xml_enviar = xml_enviar_nota_retorna_url(nfse=nfse_values)

        self.xml_to_send = base64.encodestring(xml_enviar)
        self.xml_to_send_name = 'nfse-enviar-%s.xml' % self.numero

    @api.multi
    def action_send_eletronic_invoice(self):
        super(InvoiceEletronic, self).action_send_eletronic_invoice()

        if self.model == '009':
            self.state = 'error'
            xml_to_send = base64.decodestring(self.xml_to_send)
            resposta = enviar_nota_retorna_url(
                xml=xml_to_send, ambiente=self.ambiente)

            codigo, mensagem = resposta['received_xml'].split('-')
            if codigo == '1':
                self.state = 'done'
                self.codigo_retorno = '1'
                self.mensagem_retorno = \
                    'Nota Fiscal Digital emitida com sucesso'
                self.url_danfe = mensagem
            else:
                self.codigo_retorno = codigo
                self.mensagem_retorno = mensagem

            self.env['invoice.eletronic.event'].create({
                'code': self.codigo_retorno,
                'name': self.mensagem_retorno,
                'invoice_eletronic_id': self.id,
            })

    @api.multi
    def action_cancel_document(self, context=None, justificativa=None):
        if self.model not in ('009'):
            return super(InvoiceEletronic, self).action_cancel_document(
                justificativa=justificativa)

        if self.model == '009':
            raise UserError(u'Não é possível cancelar NFSe automaticamente!')
