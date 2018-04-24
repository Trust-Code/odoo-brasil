# © 2016 Danimar Ribeiro <danimaribeiro@gmail.com>, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import re
import base64
import time
import logging
from odoo import api, fields, models
from odoo.tools.safe_eval import safe_eval

_logger = logging.getLogger(__name__)

try:
    from pytrustnfe.nfse.floripa import xml_processar_nota
    from pytrustnfe.nfse.floripa import processar_nota
    from pytrustnfe.nfse.floripa import cancelar_nota

    from pytrustnfe.certificado import Certificado
except ImportError:
    _logger.warning('Cannot import pytrustnfe', exc_info=True)


STATE = {'edit': [('readonly', False)]}


class InvoiceEletronic(models.Model):
    _inherit = 'invoice.eletronic'

    model = fields.Selection(
        selection_add=[('012', 'NFS-e Florianópolis')])

    def qrcode_floripa_url(self):
        import urllib

        url_consulta = "http://nfps-e.pmf.sc.gov.br/consulta-frontend/#!/\
consulta?cod=%s&cmc=%s" % (self.verify_code, self.company_id.inscr_mun)

        url = '<img class="center-block"\
style="max-width:90px;height:90px;margin:0px 1px;"src="/report/barcode/\
?type=QR&value=' + urllib.parse.quote(url_consulta) + '"/>'
        return url

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
            if not self.company_id.aedf:
                errors.append('Código AEDF da empresa obrigatório')

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
            aliquota = line.issqn_aliquota / 100
            base = line.issqn_base_calculo
            if self.company_id.fiscal_type != '3':
                aliquota, base = 0.0, 0.0
            unitario = round(line.valor_liquido / line.quantidade, 2)
            items.append({
                'name': line.product_id.name,
                'cnae': re.sub(
                    '[^0-9]', '', self.company_id.cnae_main_id.id_cnae or ''),
                'cst_servico': '1',
                'aliquota': aliquota,
                'base_calculo': base,
                'valor_unitario': unitario,
                'quantidade': int(line.quantidade),
                'valor_total': line.valor_liquido,
            })
        emissao = fields.Datetime.from_string(self.data_emissao)
        cfps = '9201'
        if self.company_id.city_id.id != partner.city_id.id:
            cfps = '9202'
        if self.company_id.state_id.id != partner.state_id.id:
            cfps = '9203'
        base, issqn = self.valor_bc_issqn, self.valor_issqn
        if self.company_id.fiscal_type != '3':
            base, issqn = 0.0, 0.0
        return {
            'numero': "%06d" % self.numero,
            'tomador': tomador,
            'itens_servico': items,
            'data_emissao': emissao.strftime('%Y-%m-%d'),
            'base_calculo': base,
            'valor_issqn': issqn,
            'valor_total': self.valor_final,
            'aedf': self.company_id.aedf,
            'cfps': cfps,
            'observacoes': '',
        }

    def _find_attachment_ids_email(self):
        atts = super(InvoiceEletronic, self)._find_attachment_ids_email()
        if self.model not in ('012'):
            return atts
        attachment_obj = self.env['ir.attachment']
        attachment_ids = attachment_obj.search(
            [('res_model', '=', 'invoice.eletronic'),
             ('res_id', '=', self.id),
             ('name', 'like', 'nfse-ret')], limit=1, order='id desc')

        for attachment in attachment_ids:
            xml_id = attachment_obj.create(dict(
                name=attachment.name,
                datas_fname=attachment.datas_fname,
                datas=attachment.datas,
                mimetype=attachment.mimetype,
                res_model='account.invoice',
                res_id=self.invoice_id.id,
            ))
            atts.append(xml_id.id)

        danfe_report = self.env['ir.actions.report'].search(
            [('report_name', '=',
              'br_nfse_florianopolis.main_template_br_nfse_danfpse')])
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

        if "codigoVerificacao" in dir(retorno):
            self.state = 'done'
            self.codigo_retorno = '100'
            self.mensagem_retorno = \
                'Nota Fiscal emitida com sucesso'

            self.verify_code = retorno.codigoVerificacao
            self.numero_nfse = retorno.numeroSerie
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

        if not justificativa:
            return {
                'name': 'Cancelamento NFe',
                'type': 'ir.actions.act_window',
                'res_model': 'wizard.cancel.nfse',
                'view_type': 'form',
                'view_mode': 'form',
                'target': 'new',
                'context': {
                    'default_edoc_id': self.id
                }
            }
        cert = self.company_id.with_context({'bin_size': False}).nfe_a1_file
        cert_pfx = base64.decodestring(cert)
        certificado = Certificado(cert_pfx, self.company_id.nfe_a1_password)

        company = self.company_id
        canc = {
            'motivo': justificativa,
            'aedf': re.sub('[^0-9]', '', company.aedf),
            'numero': self.numero_nfse,
            'codigo_verificacao': self.verify_code,
        }
        resposta = cancelar_nota(certificado, cancelamento=canc,
                                 ambiente=self.ambiente,
                                 client_id=self.company_id.client_id,
                                 secret_id=self.company_id.client_secret,
                                 username=self.company_id.inscr_mun,
                                 password=self.company_id.user_password)
        retorno = resposta['object']
        msg_cancelada = 'A Nota Fiscal já está com a situação cancelada.'
        if resposta['status_code'] == 200 or retorno.message == msg_cancelada:
            self.state = 'cancel'
            self.codigo_retorno = '100'
            self.mensagem_retorno = 'Nota Fiscal Cancelada'
        else:
            self.codigo_retorno = resposta['status_code']
            self.mensagem_retorno = retorno.message

        self.env['invoice.eletronic.event'].create({
            'code': self.codigo_retorno,
            'name': self.mensagem_retorno,
            'invoice_eletronic_id': self.id,
        })
        self._create_attachment(
            'canc', self, resposta['sent_xml'])
        self._create_attachment(
            'canc-ret', self, resposta['received_xml'].decode('utf-8'))
