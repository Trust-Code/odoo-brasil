# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro <danimaribeiro@gmail.com>, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import os
import tempfile
import subprocess
import re
import pytz
import base64
import logging
from datetime import datetime

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.addons.report.models.report import _get_wkhtmltopdf_bin
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
            dt_emissao = dt_emissao.strftime('%d/%m/%Y')

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

            tipo_nota = '1'  # Normal
            if self.company_id.fiscal_type == '1':
                tipo_nota = '4'  # Simples Nacional

            descricao = ''
            codigo_servico = ''
            for item in self.eletronic_item_ids:
                descricao += item.name + '\n'
                codigo_servico = item.issqn_codigo

            def fmt_number(x):
                return str("%.2f" % x).replace('.', ',')

            nfse_vals = {
                'codigo_prefeitura': '3150',
                'senha_nfd': 'fiscalb',
                'tomador': tomador,
                'prestador': prestador,
                'cnpj_prestador': prestador['cnpj'],
                'total_servicos': fmt_number(self.valor_final),
                'status_nota': tipo_nota,
                'numero': self.numero,
                'data_emissao': dt_emissao,
                'aliquota_atividade':
                fmt_number(self.eletronic_item_ids[0].issqn_aliquota),
                'codigo_atividade': codigo_servico,
                'valor_pis': fmt_number(self.valor_pis_servicos),
                'valor_cofins': fmt_number(self.valor_cofins_servicos),
                'valor_csll': fmt_number(self.valor_retencao_csll),
                'valor_inss': fmt_number(self.valor_retencao_inss),
                'valor_ir': fmt_number(self.valor_retencao_irrf),
                'aliquota_pis':
                fmt_number(self.eletronic_item_ids[0].pis_aliquota),
                'aliquota_cofins':
                fmt_number(self.eletronic_item_ids[0].cofins_aliquota),
                'aliquota_csll':
                fmt_number(self.eletronic_item_ids[0].csll_aliquota),
                'aliquota_inss':
                fmt_number(self.eletronic_item_ids[0].inss_aliquota),
                'aliquota_ir':
                fmt_number(self.eletronic_item_ids[0].irrf_aliquota),
                'valor_deducao': '0,00',
                'descricao': descricao,
                'observacoes': self.informacoes_complementares,
            }
            res.update(nfse_vals)
        return res

    def _find_attachment_ids_email(self):
        atts = super(InvoiceEletronic, self)._find_attachment_ids_email()
        attachment_obj = self.env['ir.attachment']
        if self.model not in ('009'):
            return atts

        tmp = tempfile._get_default_tempdir()
        temp_name = os.path.join(tmp, next(tempfile._get_candidate_names()))

        command_args = ["--dpi", "84", str(self.url_danfe), temp_name]
        wkhtmltopdf = [_get_wkhtmltopdf_bin()] + command_args
        process = subprocess.Popen(wkhtmltopdf, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        out, err = process.communicate()
        if process.returncode not in [0, 1]:
            raise UserError(_('Wkhtmltopdf failed (error code: %s). '
                              'Message: %s') % (str(process.returncode), err))
        tmpDanfe = None
        with open(temp_name, 'r') as f:
            tmpDanfe = f.read()

        try:
            os.unlink(temp_name)
        except (OSError, IOError):
            _logger.error('Error when trying to remove file %s' % temp_name)

        if tmpDanfe:
            danfe_id = attachment_obj.create(dict(
                name="Danfe-%08d.pdf" % self.numero,
                datas_fname="Danfe-%08d.pdf" % self.numero,
                datas=base64.b64encode(tmpDanfe),
                mimetype='application/pdf',
                res_model='account.invoice',
                res_id=self.invoice_id.id,
            ))
            atts.append(danfe_id.id)
        return atts

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
        if self.model == '009' and self.state not in ('done', 'cancel'):
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
