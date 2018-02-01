# © 2016 Danimar Ribeiro <danimaribeiro@gmail.com>, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import re
import base64
import logging
from odoo import api, fields, models

_logger = logging.getLogger(__name__)

try:
    from pytrustnfe.nfse.floripa import xml_processar_nota
    from pytrustnfe.nfse.floripa import processar_nota
    from pytrustnfe.nfse.floripa import cancelar_nota

    from pytrustnfe.certificado import Certificado
except ImportError:
    _logger.error('Cannot import pytrustnfe', exc_info=True)


STATE = {'edit': [('readonly', False)]}


class InvoiceEletronic(models.Model):
    _inherit = 'invoice.eletronic'

    model = fields.Selection(
        selection_add=[('012', 'NFS-e Florianópolis')])

    @api.multi
    def _hook_validation(self):
        errors = super(InvoiceEletronic, self)._hook_validation()
        if self.model == '012':
            if not self.company_id.client_id:
                errors.append('Client ID na empresa é obrigatório')
            if not self.company_id.client_secret:
                errors.append('Client Secret na empresa é obrigatório')
            if not self.company_id.user_password:
                errors.append('Inscrição municipal obrigatória')
            if not self.company_id.cnae_main_id.id_cnae:
                errors.append('Código de CNAE da empresa obrigatório')

        return errors

    @api.multi
    def _prepare_eletronic_invoice_values(self):
        res = super(InvoiceEletronic, self)._prepare_eletronic_invoice_values()
        if self.model != '012':
            return res
        partner = self.commercial_partner_id

        tomador = {
            'cnpj_cpf': re.sub(
                '[^0-9]', '', partner.cnpj_cpf or ''),
            'inscricao_municipal': re.sub(
                '[^0-9]', '', partner.inscr_mun or
                '0000000'),
            'razao_social': partner.legal_name or partner.name,
            'logradouro': partner.street,
            'numero': partner.number,
            'bairro': partner.district,
            'cep': re.sub('[^0-9]', '', partner.zip or ''),
            'cidade': '%s%s' % (
                partner.state_id.ibge_code,
                partner.city_id.ibge_code),
            'uf': partner.state_id.code,
            'email': self.partner_id.email,
            'phone': re.sub('[^0-9]', '', self.partner_id.phone or ''),
        }
        items = []
        for line in self.eletronic_item_ids:
            items.append({
                'name': line.product_id.name,
                'cnae': re.sub(
                    '[^0-9]', '', self.company_id.cnae_main_id.id_cnae or ''),
                'cst_servico': '1',
                'aliquota': line.issqn_aliquota / 100,
                'valor_unitario': line.preco_unitario,
                'quantidade': int(line.quantidade),
                'valor_total': line.valor_liquido,
            })
        emissao = fields.Datetime.from_string(self.data_emissao)
        cfps = '9201'
        if self.company_id.city_id.id != partner.city_id.id:
            cfps = '9202'
        if self.company_id.state_id.id != partner.state_id.id:
            cfps = '9203'
        return {
            'numero': "%06d" % self.id,
            'tomador': tomador,
            'itens_servico': items,
            'data_emissao': emissao.strftime('%Y-%m-%d'),
            'base_calculo': self.valor_bc_issqn,
            'valor_issqn': self.valor_issqn,
            'valor_total': self.valor_final,
            'aedf': self.company_id.partner_id.inscr_mun[:6],
            'cfps': cfps,
            'observacoes': '',
        }

    @api.multi
    def action_post_validate(self):
        super(InvoiceEletronic, self).action_post_validate()
        if self.model not in ('012'):
            return

        cert = self.company_id.with_context(
            {'bin_size': False}).nfe_a1_file
        cert_pfx = base64.decodestring(cert)

        certificado = Certificado(
            cert_pfx, self.company_id.nfe_a1_password)

        nfse_values = self._prepare_eletronic_invoice_values()
        xml_enviar = xml_processar_nota(certificado, rps=nfse_values)

        self.xml_to_send = base64.encodestring(xml_enviar.encode('utf-8'))
        self.xml_to_send_name = 'nfse-enviar-%s.xml' % self.numero

    @api.multi
    def action_send_eletronic_invoice(self):
        super(InvoiceEletronic, self).action_send_eletronic_invoice()
        if self.model != '012' or self.state in ('done', 'cancel'):
            return

        self.state = 'error'
        xml_to_send = base64.decodestring(self.xml_to_send)

        recebe_lote = processar_nota(
            None, xml=xml_to_send, ambiente=self.ambiente,
            client_id=self.company_id.client_id,
            secret_id=self.company_id.client_secret,
            username=self.company_id.inscr_mun,
            password=self.company_id.user_password)

        retorno = recebe_lote['object']

        if "codigo" in dir(retorno):
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

        else:
            self.codigo_retorno = recebe_lote['status_code']
            self.mensagem_retorno = retorno.message

        self.env['invoice.eletronic.event'].create({
            'code': self.codigo_retorno,
            'name': self.mensagem_retorno,
            'invoice_eletronic_id': self.id,
        })
        self._create_attachment(
            'nfse-envio', self, recebe_lote['sent_xml'].decode('utf-8'))
        self._create_attachment(
            'nfse-ret', self, recebe_lote['received_xml'].decode('utf-8'))

    @api.multi
    def action_cancel_document(self, context=None, justificativa=None):
        if self.model not in ('012'):
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
        resposta = cancelar_nota(certificado, cancelamento=canc)
        retorno = resposta['object']
        if retorno.Cabecalho.Sucesso:
            self.state = 'cancel'
            self.codigo_retorno = '100'
            self.mensagem_retorno = 'Nota Fiscal Cancelada'
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
