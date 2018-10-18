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
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DTFT

_logger = logging.getLogger(__name__)

try:
    from pytrustnfe.nfse.paulistana import envio_lote_rps
    from pytrustnfe.nfse.paulistana import teste_envio_lote_rps
    from pytrustnfe.nfse.paulistana import cancelamento_nfe
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
    def _compute_discriminacao(self):
        for item in self:
            descricao = ''
            for line in item.eletronic_item_ids:
                descricao += line.name.replace('\n', '<br/>') + '<br/>'
            if item.informacoes_legais:
                descricao += item.informacoes_legais.replace('\n', '<br/>')
            item.discriminacao_servicos = descricao

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
        default='T', readonly=True, states=STATE)
    verify_code = fields.Char(
        string=u'Código Autorização', size=20, readonly=True, states=STATE)
    numero_nfse = fields.Char(
        string=u"Número NFSe", size=50, readonly=True, states=STATE)

    discriminacao_servicos = fields.Char(compute='_compute_discriminacao')

    def issqn_due_date(self):
        date_emition = datetime.strptime(self.data_emissao, DTFT)
        next_month = date_emition + relativedelta(months=1)
        due_date = date(next_month.year, next_month.month, 10)
        if due_date.weekday() >= 5:
            while due_date.weekday() != 0:
                due_date = due_date + timedelta(days=1)
        format = "%d/%m/%Y"
        due_date = datetime.strftime(due_date, format)
        return due_date

    @api.multi
    def _hook_validation(self):
        errors = super(InvoiceEletronic, self)._hook_validation()
        if self.model == '001':
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
                    if not eletr.codigo_servico_paulistana:
                        errors.append(u'%s - Código da NFSe paulistana não \
                                      configurado' % prod)
                if not eletr.pis_cst:
                    errors.append(u'%s - CST do PIS' % prod)
                if not eletr.cofins_cst:
                    errors.append(u'%s - CST do Cofins' % prod)

        return errors

    @api.multi
    def _prepare_eletronic_invoice_values(self):
        res = super(InvoiceEletronic, self)._prepare_eletronic_invoice_values()
        if self.model == '001':
            tz = pytz.timezone(self.env.user.partner_id.tz) or pytz.utc
            dt_emissao = datetime.strptime(self.data_emissao, DTFT)
            dt_emissao = pytz.utc.localize(dt_emissao).astimezone(tz)
            dt_emissao = dt_emissao.strftime('%Y-%m-%d')

            partner = self.commercial_partner_id
            city_tomador = partner.city_id
            tomador = {
                'tipo_cpfcnpj': 2 if partner.is_company else 1,
                'cpf_cnpj': re.sub('[^0-9]', '',
                                   partner.cnpj_cpf or ''),
                'razao_social': partner.legal_name or partner.name,
                'logradouro': partner.street or '',
                'numero': partner.number or '',
                'complemento': partner.street2 or '',
                'bairro': partner.district or 'Sem Bairro',
                'cidade': '%s%s' % (city_tomador.state_id.ibge_code,
                                    city_tomador.ibge_code),
                'cidade_descricao': city_tomador.name or '',
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
                'razao_social': self.company_id.partner_id.legal_name or '',
                'inscricao_municipal': re.sub(
                    '[^0-9]', '', self.company_id.partner_id.inscr_mun or ''),
                'cidade': '%s%s' % (city_prestador.state_id.ibge_code,
                                    city_prestador.ibge_code),
                'telefone': re.sub('[^0-9]', '', self.company_id.phone or ''),
                'email': self.company_id.partner_id.email or '',
            }

            descricao = ''
            codigo_servico = ''
            for item in self.eletronic_item_ids:
                descricao += item.name.replace('\n', '|') + '|'
                codigo_servico = item.codigo_servico_paulistana

            if self.informacoes_legais:
                descricao += self.informacoes_legais.replace('\n', '|')

            rps = {
                'tomador': tomador,
                'prestador': prestador,
                'numero': self.numero,
                'data_emissao': dt_emissao,
                'serie': self.serie.code or '',
                'aliquota_atividade':
                    "%.3f" % self.eletronic_item_ids[0].issqn_aliquota,
                'codigo_atividade': re.sub('[^0-9]', '', codigo_servico or ''),
                'municipio_prestacao': city_prestador.name or '',
                'valor_pis': "%.2f" % self.valor_retencao_pis,
                'valor_cofins': "%.2f" % self.valor_retencao_cofins,
                'valor_csll': "%.2f" % self.valor_retencao_csll,
                'valor_inss': "%.2f" % self.valor_retencao_inss,
                'valor_ir': "%.2f" % self.valor_retencao_irrf,
                'valor_servico': "%.2f" % self.valor_final,
                'valor_deducao': '0',
                'descricao': descricao,
                'deducoes': [],
                'valor_carga_tributaria':
                "%.2f" % self.valor_estimado_tributos,
                'fonte_carga_tributaria': 'IBPT',
                'iss_retido':
                    'true' if self.valor_retencao_issqn > 0.0 else 'false'
            }

            valor_servico = self.valor_final
            valor_deducao = 0.0

            cnpj_cpf = tomador['cpf_cnpj']
            data_envio = rps['data_emissao']
            inscr = prestador['inscricao_municipal']
            iss_retido = 'S' if self.valor_retencao_issqn > 0.0 else 'N'
            tipo_cpfcnpj = tomador['tipo_cpfcnpj']
            codigo_atividade = rps['codigo_atividade']
            tipo_recolhimento = self.operation  # T – Tributado em São Paulo

            assinatura = '%s%s%s%s%sN%s%015d%015d%s%s%s' % (
                str(inscr).zfill(8),
                self.serie.code.ljust(5),
                str(self.numero).zfill(12),
                str(data_envio[0:4] + data_envio[5:7] + data_envio[8:10]),
                str(tipo_recolhimento),
                str(iss_retido),
                round(valor_servico * 100),
                round(valor_deducao * 100),
                str(codigo_atividade).zfill(5),
                str(tipo_cpfcnpj),
                str(cnpj_cpf).zfill(14)
            )
            rps['assinatura'] = assinatura

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
                'lista_rps': [rps]
            }

            res.update(nfse_vals)
        return res

    def _find_attachment_ids_email(self):
        atts = super(InvoiceEletronic, self)._find_attachment_ids_email()
        if self.model not in ('001'):
            return atts

        attachment_obj = self.env['ir.attachment']
        danfe_report = self.env['ir.actions.report.xml'].search(
            [('report_name', '=', 'br_nfse.main_template_br_nfse_danfe')])
        report_service = danfe_report.report_name
        danfse = self.env['report'].get_pdf([self.id], report_service)
        if danfse:
            danfe_id = attachment_obj.create(dict(
                name="paulistana-%08d.pdf" % self.numero,
                datas_fname="paulistana-%08d.pdf" % self.numero,
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
        if self.model == '001' and self.state not in ('done', 'cancel'):
            self.state = 'error'

            nfse_values = self._prepare_eletronic_invoice_values()
            cert = self.company_id.with_context(
                {'bin_size': False}).nfe_a1_file
            cert_pfx = base64.decodestring(cert)

            certificado = Certificado(
                cert_pfx, self.company_id.nfe_a1_password)

            if self.ambiente == 'producao':
                resposta = envio_lote_rps(certificado, nfse=nfse_values)
            else:
                resposta = teste_envio_lote_rps(
                    certificado, nfse=nfse_values)
            retorno = resposta['object']
            if retorno.Cabecalho.Sucesso:
                self.state = 'done'
                self.codigo_retorno = '100'
                self.mensagem_retorno = \
                    'Nota Fiscal Paulistana emitida com sucesso'

                # Apenas producão tem essa tag
                if self.ambiente == 'producao':
                    self.verify_code = \
                        retorno.ChaveNFeRPS.ChaveNFe.CodigoVerificacao
                    self.numero_nfse = retorno.ChaveNFeRPS.ChaveNFe \
                        .NumeroNFe

                for inv_line in self.invoice_id.invoice_line_ids:
                    if inv_line.product_id.fiscal_type == 'service':
                        inv_line.write(
                            {'state': 'transmitido',
                             'numero_nfse': self.numero_nfse})

            else:
                self.codigo_retorno = retorno.Erro.Codigo
                self.mensagem_retorno = retorno.Erro.Descricao

            self.env['invoice.eletronic.event'].create({
                'code': self.codigo_retorno,
                'name': self.mensagem_retorno,
                'invoice_eletronic_id': self.id,
            })
            self._create_attachment(
                'nfse-envio', self, resposta['sent_xml'])
            self._create_attachment(
                'nfse-ret', self, resposta['received_xml'])

    @api.multi
    def action_cancel_document(self, context=None, justificativa=None):
        if self.model not in ('001'):
            return super(InvoiceEletronic, self).action_cancel_document(
                justificativa=justificativa)

        cert = self.company_id.with_context({'bin_size': False}).nfe_a1_file
        cert_pfx = base64.decodestring(cert)
        certificado = Certificado(cert_pfx, self.company_id.nfe_a1_password)

        if self.ambiente == 'homologacao' or \
           self.company_id.tipo_ambiente_nfse == 'homologacao':
            self.state = 'cancel'
            self.codigo_retorno = '100'
            self.mensagem_retorno = 'Nota Fiscal Paulistana Cancelada'
            return
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
        resposta = cancelamento_nfe(certificado, cancelamento=canc)
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
