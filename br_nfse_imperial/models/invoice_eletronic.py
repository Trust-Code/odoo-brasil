# © 2017 Danimar Ribeiro <danimaribeiro@gmail.com>, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import re
import requests
import base64
import logging
from odoo import api, fields, models
from odoo.exceptions import UserError


_logger = logging.getLogger(__name__)

try:
    from pytrustnfe.nfse.imperial import gerar_nota
    from pytrustnfe.nfse.imperial import xml_gerar_nota
    from pytrustnfe.nfse.imperial import cancelar_nota
except ImportError:
    _logger.error('Cannot import pytrustnfe', exc_info=True)


STATE = {'edit': [('readonly', False)]}


class InvoiceEletronic(models.Model):
    _inherit = 'invoice.eletronic'

    url_danfe = fields.Char(
        string='Url de Impressão Danfe', size=500, readonly=True)

    @api.multi
    def _hook_validation(self):
        errors = super(InvoiceEletronic, self)._hook_validation()
        if self.model == '010':
            issqn_codigo = ''
            if not self.company_id.senha_nfse_imperial:
                errors.append('Senha do contribuinte obrigatória')
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

            descricao = ''
            codigo_servico = ''
            for item in self.eletronic_item_ids:
                descricao += item.name + '\n'
                codigo_servico = item.issqn_codigo

            partner = self.commercial_partner_id
            company = self.company_id
            nota_fiscal = {
                'ccm': re.sub('[^0-9]', '', company.inscr_mun),
                'cnpj': re.sub('[^0-9]', '', company.cnpj_cpf),
                'senha': company.senha_nfse_imperial,
                'aliquota_simples': company.iss_simples_nacional,

                'situacao': 'tp',  # Tributada no prestador
                'servico': int(re.sub('[^0-9]', '', codigo_servico)),
                'descricaoNF': descricao,

                'base': self.valor_final,
                'valor': self.valor_final,

                'tomador_tipo': 2 if not partner.is_company else 4,
                'tomador_cnpj': re.sub('[^0-9]', '', partner.cnpj_cpf or ''),
                'tomador_email': self.partner_id.email or partner.email or '',
                'tomador_ie': partner.inscr_est or '',
                'tomador_razao': partner.legal_name or partner.name or '',
                'tomador_fantasia': partner.name or '',
                'tomador_endereco': partner.street or '',
                'tomador_numero': partner.number or '',
                'tomador_complemento': partner.street2 or '',
                'tomador_bairro': partner.district or 'Sem Bairro',
                'tomador_cod_cidade': '%s%s' % (partner.state_id.ibge_code,
                                                partner.city_id.ibge_code),
                'tomador_CEP': re.sub('[^0-9]', '', partner.zip),
                'tomador_fone': re.sub('[^0-9]', '', partner.phone or ''),

                'retencao_iss': self.valor_retencao_issqn,
                'pis': self.valor_retencao_pis,
                'cofins': self.valor_retencao_cofins,
                'inss': self.valor_retencao_inss,
                'irrf': self.valor_retencao_irrf,
                'csll': self.valor_retencao_pis,
            }
            res.update(nota_fiscal)
        return res

    def _find_attachment_ids_email(self):
        atts = super(InvoiceEletronic, self)._find_attachment_ids_email()
        attachment_obj = self.env['ir.attachment']
        if self.model not in ('010'):
            return atts

        response = requests.get(self.url_danfe)

        if response.ok:
            danfe_id = attachment_obj.create(dict(
                name="Danfe-%08d.pdf" % self.numero,
                datas_fname="Danfe-%08d.pdf" % self.numero,
                datas=base64.b64encode(response.content),
                mimetype='application/pdf',
                res_model='account.invoice',
                res_id=self.invoice_id.id,
            ))
            atts.append(danfe_id.id)
        return atts

    @api.multi
    def action_post_validate(self):
        super(InvoiceEletronic, self).action_post_validate()
        if self.model not in ('010'):
            return

        nfse_values = self._prepare_eletronic_invoice_values()
        xml_enviar = xml_gerar_nota(None, nfse=nfse_values)

        self.xml_to_send = base64.encodestring(xml_enviar)
        self.xml_to_send_name = 'nfse-enviar-%s.xml' % self.numero

    @api.multi
    def action_send_eletronic_invoice(self):
        super(InvoiceEletronic, self).action_send_eletronic_invoice()
        if self.model != '010' or self.state in ('done', 'cancel'):
            return

        self.state = 'error'

        xml_to_send = base64.decodestring(self.xml_to_send)
        dic_retorno = gerar_nota(None, xml=xml_to_send, ambiente=self.ambiente)

        obj = dic_retorno['object'].GerarNotaResponse
        if obj.RetornoNota.Resultado == 1:
            self.state = 'done'
            self.codigo_retorno = '1'
            self.mensagem_retorno = \
                'Nota Fiscal Digital emitida com sucesso'
            self.recibo_nfe = obj.RetornoNota.autenticidade
            self.numero_nfse = obj.RetornoNota.Nota
            self.url_danfe = obj.RetornoNota.LinkImpressao

        else:
            self.codigo_retorno = 0
            self.mensagem_retorno = obj.DescricaoErros.item[0].DescricaoErro

        self.env['invoice.eletronic.event'].create({
            'code': self.codigo_retorno,
            'name': self.mensagem_retorno,
            'invoice_eletronic_id': self.id,
        })
        self._create_attachment('nfse-ret', self, dic_retorno['received_xml'])

    @api.multi
    def action_cancel_document(self, context=None, justificativa=None):
        if self.model not in ('010'):
            return super(InvoiceEletronic, self).action_cancel_document(
                justificativa=justificativa)

        if not justificativa:
            return {
                'name': 'Cancelamento NFSe',
                'type': 'ir.actions.act_window',
                'res_model': 'wizard.cancel.nfse',
                'view_type': 'form',
                'view_mode': 'form',
                'target': 'new',
                'context': {
                    'default_edoc_id': self.id
                }
            }

        partner = self.commercial_partner_id
        canc = {
            'ccm': re.sub('[^0-9]', '',  self.company_id.inscr_mun),
            'cnpj': re.sub('[^0-9]', '',  self.company_id.cnpj_cpf),
            'senha':  self.company_id.senha_nfse_imperial,
            'nota': self.numero_nfse,
            'tomador_email': self.partner_id.email or partner.email or '',
            'motivo': justificativa,
        }
        dic_retorno = cancelar_nota(
            None, cancelamento=canc, ambiente=self.ambiente)

        obj = dic_retorno['object'].CancelarNotaResponse
        if obj.RetornoNota.Resultado == 1:
            self.state = 'cancel'
            self.codigo_retorno = '100'
            self.mensagem_retorno = 'Nota Fiscal de Serviço Cancelada'
        else:
            raise UserError(obj.DescricaoErros.item[0].DescricaoErro)

        self.env['invoice.eletronic.event'].create({
            'code': self.codigo_retorno,
            'name': self.mensagem_retorno,
            'invoice_eletronic_id': self.id,
        })
        self._create_attachment('canc', self, dic_retorno['sent_xml'])
        self._create_attachment('canc-ret', self, dic_retorno['received_xml'])
