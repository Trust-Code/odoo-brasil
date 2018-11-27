# -*- coding: utf-8 -*-
# © 2017 Danimar Ribeiro <danimaribeiro@gmail.com>, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import re
import pytz
import time
import base64
import logging
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DTFT
from odoo.tools.safe_eval import safe_eval

_logger = logging.getLogger(__name__)

try:
    from pytrustnfe.nfse.imperial import xml_processa_rps
    from pytrustnfe.nfse.imperial import processa_rps
    from pytrustnfe.nfse.imperial import consulta_protocolo
    from pytrustnfe.nfse.imperial import consulta_notas_protocolo
    from pytrustnfe.nfse.imperial import cancelar_nfse
except ImportError:
    _logger.error('Cannot import pytrustnfe', exc_info=True)


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
            tomador = {
                'tipo_cpfcnpj': 2 if partner.is_company else 1,
                'cnpj_cpf': re.sub('[^0-9]', '',
                                   partner.cnpj_cpf or ''),
                'razao_social': partner.legal_name or partner.name or '',
                'logradouro': partner.street or '',
                'numero': partner.number or '',
                'complemento': partner.street2 or '',
                'bairro': partner.district or 'Sem Bairro',
                'municipio': partner.city_id.name,
                'uf': partner.state_id.code,
                'cep': re.sub('[^0-9]', '', partner.zip),
                'telefone': re.sub('[^0-9]', '', partner.phone or ''),
                'inscricao_municipal': re.sub(
                    '[^0-9]', '', partner.inscr_mun or ''),
                'email': self.partner_id.email or partner.email or '',
            }
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
            descricao = ''
            codigo_servico = ''
            for item in self.eletronic_item_ids:
                descricao += item.name + '\n'
                codigo_servico = item.issqn_codigo

            impostos = []
            if self.valor_retencao_cofins:
                impostos.append({
                    'sigla': 'COFINS',
                    'aliquota': self.eletronic_item_ids[0].cofins_aliquota,
                    'valor': self.valor_retencao_cofins
                })
            if self.valor_retencao_csll:
                impostos.append({
                    'sigla': 'CSLL',
                    'aliquota': self.eletronic_item_ids[0].pis_aliquota,
                    'valor': self.valor_retencao_csll
                })
            if self.valor_retencao_inss:
                impostos.append({
                    'sigla': 'INSS',
                    'aliquota': self.eletronic_item_ids[0].inss_aliquota,
                    'valor': self.valor_retencao_inss
                })
            if self.valor_retencao_irrf:
                impostos.append({
                    'sigla': 'IR',
                    'aliquota': self.eletronic_item_ids[0].irrf_aliquota,
                    'valor': self.valor_retencao_irrf
                })
            if self.valor_retencao_inss:
                impostos.append({
                    'sigla': 'ISS',
                    'aliquota': self.eletronic_item_ids[0].issqn_aliquota,
                    'valor': self.valor_retencao_issqn
                })
            if self.valor_retencao_pis:
                impostos.append({
                    'sigla': 'PIS',
                    'aliquota': self.eletronic_item_ids[0].pis_aliquota,
                    'valor': self.valor_retencao_pis
                })

            rps = {
                'tipo_nfse': 'RPS',
                'numero': self.numero,
                'serie': self.serie.code or '',
                'data_emissao': dt_emissao.strftime('%d/%m/%Y'),
                'valor_servico': self.valor_final,
                'valor_deducao': 0.0,
                'iss_retido':
                'SIM' if self.valor_retencao_issqn > 0 else 'NAO',
                'valor_iss': self.valor_issqn,
                'valor_iss_retido': self.valor_retencao_issqn,
                'base_calculo': self.valor_final,
                'aliquota_issqn': self.eletronic_item_ids[0].issqn_aliquota,
                'valor_liquido_nfse': self.valor_final,
                'codigo_servico': codigo_servico,
                'descricao': descricao,
                'tomador': tomador,
                'prestador': prestador,
                'impostos': impostos,
            }

            adesao = fields.Date.from_string(
                self.company_id.adesao_simples_nacional)
            nfse_vals = {
                'ano': dt_emissao.strftime('%Y'),
                'mes': dt_emissao.strftime('%m'),
                'data_emissao': dt_emissao.strftime('%d/%m/%Y'),
                'tipo_tributacao': self.company_id.tipo_tributacao_imperial,
                'aliquota_simples_isencao':
                self.company_id.iss_simples_nacional,
                'data_adesao_simples':
                adesao and adesao.strftime('%d/%m/%Y') or '',
                'cnpj_prestador': prestador['cnpj'],
                'lista_rps': [rps],
                'valor_tributos': valor_tributos,
                'quantidade_impostos': len(impostos),
                'codigo_usuario': self.company_id.codigo_nfse_usuario,
                'codigo_contribuinte': self.company_id.codigo_nfse_empresa,
            }

            res.update(nfse_vals)
        return res

    def _find_attachment_ids_email(self):
        atts = super(InvoiceEletronic, self)._find_attachment_ids_email()
        if self.model not in ('010'):
            return atts
        attachment_obj = self.env['ir.attachment']

        danfe_report = self.env['ir.actions.report'].search(
            [('report_name', '=',
              'br_nfse_imperial.main_template_br_nfse_danfe_imperial')])
        report_service = danfe_report.xml_id
        danfse, dummy = self.env.ref(report_service).render_qweb_pdf([self.id])
        report_name = safe_eval(danfe_report.print_report_name,
                                {'object': self, 'time': time})
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
        if self.model != '010' or self.state in ('done', 'cancel'):
            return

        self.state = 'error'

        recebe_lote = ret_consulta = None

        xml_to_send = base64.decodestring(self.xml_to_send)
        recebe_lote = processa_rps(
            None, xml=xml_to_send, ambiente=self.ambiente)

        retorno = recebe_lote['object'].Body['ws_nfe.PROCESSARPSResponse']
        retorno = retorno['Sdt_processarpsout']

        if retorno.Retorno:
            obj = {
                'protocolo': retorno.Protocolo,
                'codigo_usuario': self.company_id.codigo_nfse_usuario,
                'codigo_contribuinte': self.company_id.codigo_nfse_empresa,
            }
            self.recibo_nfe = retorno.Protocolo
            while True:
                time.sleep(2)
                ret_consulta = consulta_protocolo(
                    None, ambiente=self.ambiente, consulta=obj)

                retorno = ret_consulta['object'].Body
                retorno = retorno['ws_nfe.CONSULTAPROTOCOLOResponse']
                retorno = retorno['Sdt_consultaprotocoloout']
                if retorno.PrtXSts in (3, 4, 5):
                    break

            ret_consulta = consulta_notas_protocolo(
                None, ambiente=self.ambiente, consulta=obj)

            retorno = ret_consulta['object'].Body
            retorno = retorno['ws_nfe.CONSULTANOTASPROTOCOLOResponse']
            retorno = retorno['Sdt_consultanotasprotocoloout']

            if retorno.Retorno:
                self.state = 'done'
                self.codigo_retorno = '100'
                self.mensagem_retorno = 'NFSe emitida com sucesso'
                self.numero_nfse = retorno.XML_Notas.Reg20.Reg20Item.NumNf
                self.verify_code = \
                    retorno.XML_Notas.Reg20.Reg20Item.CodVernf
            else:
                self.codigo_retorno = '-1'
                self.mensagem_retorno = \
                    retorno.Messages.Message[1].Description

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
        if ret_consulta:
            self._create_attachment(
                'nfse-prot', self, ret_consulta['received_xml'])

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

        canc = {
            'serie_nota': 'NFE',
            'numero_nota': self.numero_nfse,
            'serie_rps': self.serie_documento,
            'numero_rps': self.numero,
            'valor': self.valor_final,
            'motivo': justificativa,
            'cancelar_guia': 'S',
            'codigo_usuario': self.company_id.codigo_nfse_usuario,
            'codigo_contribuinte': self.company_id.codigo_nfse_empresa,
        }
        cancel = cancelar_nfse(
            None, cancelamento=canc, ambiente=self.ambiente)

        retorno = cancel['object'].Body['ws_nfe.CANCELANOTAELETRONICAResponse']
        retorno = retorno['Sdt_retornocancelanfe']
        if retorno.Retorno:
            self.state = 'cancel'
            self.codigo_retorno = '100'
            self.mensagem_retorno = u'Nota Fiscal de Serviço Cancelada'
        else:
            raise UserError(retorno.Messages.Message.Description)

        self.env['invoice.eletronic.event'].create({
            'code': self.codigo_retorno,
            'name': self.mensagem_retorno,
            'invoice_eletronic_id': self.id,
        })
        self._create_attachment('canc', self, cancel['sent_xml'])
        self._create_attachment('canc-ret', self, cancel['received_xml'])

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
