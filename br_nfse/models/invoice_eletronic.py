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
    from pytrustnfe.nfse.paulistana import envio_lote_rps
    from pytrustnfe.certificado import Certificado
except ImportError:
    _logger.debug('Cannot import pytrustnfe')


FIELD_STATE = {'draft': [('readonly', False)]}


class InvoiceEletronic(models.Model):
    _inherit = 'invoice.eletronic'

    operation = fields.Selection(
        [('T', u"Tributado em São Paulo"),
         ('F', u"Tributado Fora de São Paulo"),
         ('A', u"Tributado em São Paulo, porém isento"),
         ('B', u"Tributado Fora de São Paulo, porém isento"),
         ('M', u"Tributado em São Paulo, porém Imune"),
         ('N', u"Tributado Fora de São Paulo, porém Imune"),
         ('X', u"Tributado em São Paulo, porém Exigibilidade Suspensa"),
         ('V', u"Tributado Fora de São Paulo, porém Exigibilidade Suspensa"),
         ('P', u"Exportação de Serviços"),
         ('C', u"Cancelado")], u"Operação",
        default='T', readonly=True)
    verify_code = fields.Char(u'Código Autorização', size=20,
                              readonly=True, states=FIELD_STATE)
    numero_nfse = fields.Char(string="Número NFSe", size=50)

    @api.multi
    def _hook_validation(self):
        errors = super(InvoiceEletronic, self)._hook_validation()
        if self.model == '001':
            for eletr in self.eletronic_item_ids:
                prod = u"Produto: %s - %s" % (eletr.product_id.default_code,
                                              eletr.product_id.name)
                if eletr.tipo_produto == 'service':
                    if not eletr.issqn_codigo:
                        errors.append(u'%s - Código de Serviço' % prod)
                if not eletr.pis_cst:
                    errors.append(u'%s - CST do PIS' % prod)
                if not eletr.cofins_cst:
                    errors.append(u'%s - CST do Cofins' % prod)

        return errors

    @api.multi
    def _prepare_eletronic_invoice_item(self, item, invoice):
        res = super(InvoiceEletronic, self)._prepare_eletronic_invoice_item(
            item, invoice)
        if self.model == '001':
            servico = {
                'valor_servico': item.valor_liquido,
                'valor_deducao': 0.0,
                'valor_pis': item.pis_valor,
                'valor_cofins': item.cofins_valor,
                'valor_inss': 0.0,
                'valor_ir': 0.0,
                'valor_csll': 0.0,
                'valor_retencao': 0.0,
                'valor_iss_retido': item.issqn_valor_retencao,
                'item_lista_servico': item.issqn_codigo,
                'item_codigo': '000',
                'descricao_servico': item.name,
                'codigo_municipio': '00',
                'municipio_prestacao': '00',
            }
            res.update(servico)
        return res

    @api.multi
    def _prepare_eletronic_invoice_values(self):
        res = super(InvoiceEletronic, self)._prepare_eletronic_invoice_values()
        if self.model == '001':
            tz = pytz.timezone(self.env.user.partner_id.tz) or pytz.utc
            dt_emissao = datetime.strptime(self.data_emissao, DTFT)
            dt_emissao = pytz.utc.localize(dt_emissao).astimezone(tz)

            city_tomador = self.partner_id.l10n_br_city_id
            tomador = {
                'tipo_cpfcnpj': 2 if self.partner_id.is_company else 1,
                'cpf_cnpj': re.sub('[^0-9]', '',
                                   self.partner_id.cnpj_cpf or ''),
                'razao_social': self.partner_id.legal_name or '',
                'logradouro': self.partner_id.street or '',
                'numero': self.partner_id.number or '',
                'complemento': self.partner_id.street2 or '',
                'bairro': self.partner_id.district or 'Sem Bairro',
                'cidade': '%s%s' % (city_tomador.state_id.ibge_code,
                                    city_tomador.ibge_code),
                'cidade_descricao': self.partner_id.l10n_br_city_id.name or '',
                'uf': self.partner_id.state_id.code,
                'cep': re.sub('[^0-9]', '', self.partner_id.zip),
                'telefone': re.sub('[^0-9]', '', self.partner_id.phone or ''),
                'inscricao_municipal': re.sub(
                    '[^0-9]', '', self.partner_id.inscr_mun or ''),
                'email': self.partner_id.email or '',
            }
            city_prestador = self.company_id.partner_id.city_id
            prestador = {
                'cnpj': re.sub(
                    '[^0-9]', '', self.company_id.partner_id.cnpj_cpf or ''),
                'razao_social': self.company_id.partner_id.legal_name or '',
                'inscricao_municipal': re.sub(
                    '[^0-9]', '', self.company_id.partner_id.inscr_mun or ''),
                'cidade': '%s%s' % (city_prestador.state_id.ibge_code,
                                    city_prestador.ibge_code),
                'telefone': re.sub('[^0-9]', '', self.company_id.phone or ''),
                'email': self.company_id.partner_id.email or '',
            }

            rps = [{
                'tomador': tomador,
                'prestador': prestador,
                'numero': self.numero,
                'data_emissao': dt_emissao,
                'serie': self.serie.code or '',
                'aliquota_atividade': '0.000',
                'municipio_prestacao': self.company_id,
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
                'valor_servico': str("%.2f" % self.valor_final),
                'valor_deducao': '0',
                'descricao': self.informacoes_complementares,
                'deducoes': [],
            }]

            nfse_vals = {
                'cidade': prestador['cidade'],
                'cpf_cnpj': prestador['cnpj'],
                'remetente': prestador['razao_social'],
                'transacao': '',
                'data_inicio': dt_emissao,
                'data_fim': dt_emissao,
                'total_rps': '1',
                'total_servicos': str("%.2f" % self.valor_final),
                'total_deducoes': '0',
                'lote_id': '%s' % self.code,
                'lista_rps': rps
            }

            res.update(nfse_vals)
        return res

    @api.multi
    def action_send_eletronic_invoice(self):
        super(InvoiceEletronic, self).action_send_eletronic_invoice()
        if self.model == '001':
            self.ambiente = 'homologacao'  # Evita esquecimentos
            self.state = 'error'

            nfse_values = self._prepare_eletronic_invoice_values()
            cert = self.company_id.with_context(
                {'bin_size': False}).nfe_a1_file
            cert_pfx = base64.decodestring(cert)

            certificado = Certificado(
                cert_pfx, self.company_id.nfe_a1_password)

            resposta = envio_lote_rps(certificado, **nfse_values)
            retorno = resposta['object']

            if retorno.cStat != 104:
                self.codigo_retorno = retorno.cStat
                self.mensagem_retorno = retorno.xMotivo
            else:
                self.codigo_retorno = retorno.protNFe.infProt.cStat
                self.mensagem_retorno = retorno.protNFe.infProt.xMotivo
                if self.codigo_retorno == '100':
                    self.write({'state': 'done', 'nfe_exception': False})
                # Duplicidade de NF-e significa que a nota já está emitida
                # TODO Buscar o protocolo de autorização, por hora só finalizar
                if self.codigo_retorno == '204':
                    self.write({
                        'state': 'done', 'codigo_retorno': '100',
                        'nfe_exception': False,
                        'mensagem_retorno': 'Autorizado o uso da NFSe'})

            self.env['invoice.eletronic.event'].create({
                'code': self.codigo_retorno,
                'name': self.mensagem_retorno,
                'invoice_eletronic_id': self.id,
            })
            self._create_attachment('nfse-envio', self, resposta['sent_xml'])
            self._create_attachment('nfse-ret', self, resposta['received_xml'])
