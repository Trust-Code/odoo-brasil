# © 2016 Danimar Ribeiro <danimaribeiro@gmail.com>, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import re
import pytz
import base64
import logging
import hashlib
from datetime import datetime
from odoo import api, models, fields
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DTFT

_logger = logging.getLogger(__name__)

try:
    from pytrustnfe.nfse.dsf import cancelar
    from pytrustnfe.nfse.dsf import enviar
    from pytrustnfe.nfse.dsf import teste_enviar
    from pytrustnfe.nfse.dsf import consulta_lote
    from pytrustnfe.certificado import Certificado
except ImportError:
    _logger.debug('Cannot import pytrustnfe')


STATE = {'edit': [('readonly', False)]}


class InvoiceEletronic(models.Model):
    _inherit = 'invoice.eletronic'

    model = fields.Selection(
        selection_add=[('011', 'NFS-e - Provedor DSF')])

    type_retention = fields.Selection([('A', u'ISS a recolher pelo prestador'),
                                       ('R', u'Retido na Fonte')],
                                      string='Tipo Recolhimento', default='A',
                                      readonly=True, states=STATE)

    operation = fields.Selection([('A', u"Sem Dedução"),
                                  ('B', u"Com dedução/Materiais"),
                                  ('C', u"Imune/Isenta de ISSQN"),
                                  ('D', u"Devolução/Simples Remessa"),
                                  ('J', u"Intermediação")],
                                 string="Operação",
                                 readonly=True, states=STATE)

    taxation = fields.Selection([('C', u"Isenta de ISS"),
                                 ('E', u"Não incidência no município"),
                                 ('F', u"Imune"),
                                 ('K', u"Exigibilidade Susp.Dec.J/Proc.A"),
                                 ('N', u"Não Tributável"),
                                 ('T', u"Tributável"),
                                 ('G', u"Tributável Fixo"),
                                 ('H', u"Tributável S.N."),
                                 ('M', u"Micro Empreendedor Individual(MEI)")],
                                string="Tributação",
                                readonly=True, states=STATE)

    @api.multi
    def _hook_validation(self):
        errors = super(InvoiceEletronic, self)._hook_validation()
        if self.model == '011':
            issqn_codigo = ''
            if not self.company_id.inscr_mun:
                errors.append(u'Inscrição municipal obrigatória')
            if not self.company_id.cnae_main_id.code:
                errors.append(u'CNAE Principal da empresa obrigatório')
            if len(self.company_id.phone) == 0:
                errors.append(u'Telefone da empresa obrigatório')
            if len(self.partner_id.phone) == 0:
                errors.append(u'Telefone do cliente obrigatório')
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
        if self.model == '011':
            tz = pytz.timezone(self.env.user.partner_id.tz) or pytz.utc
            dt_emissao = datetime.strptime(self.data_emissao, DTFT)
            dt_emissao = pytz.utc.localize(dt_emissao).astimezone(tz)
            dt_emissao = dt_emissao.strftime('%Y-%m-%dT%H:%M:%S')
            numero_rps = self.serie.internal_sequence_id.next_by_id()

            partner = self.commercial_partner_id
            city_tomador = partner.city_id
            partner_phone = None
            partner_ddd = None
            if partner.phone:
                partner_phone = re.sub('[^0-9]', '', partner.phone)
                partner_ddd = partner_phone[:2]
                partner_phone = partner_phone[2:]

            im_tomador = ''
            dsf_cities = ['Campinas', 'Campo Grande', 'São Luís', 'Sorocaba',
                          'Belém', 'Uberlândia', 'Teresina']
            if city_tomador.name in dsf_cities:
                im_tomador = re.sub(
                    '[^0-9]', '', partner.inscr_mun or '').zfill(9)

            tomador = {
                'cpf_cnpj': re.sub('[^0-9]', '',
                                   partner.cnpj_cpf or ''),
                'razao_social': partner.legal_name or '',
                'logradouro': partner.street or '',
                'numero': partner.number or '',
                'complemento': partner.street2 or '',
                'bairro': partner.district or 'Sem Bairro',
                'cidade': '6291',
                'cidade_descricao': partner.name or '',
                'uf': partner.state_id.code,
                'cep': re.sub('[^0-9]', '', partner.zip),
                'tipo_logradouro': 'Rua',
                'tipo_bairro': 'Normal',
                'ddd': partner_ddd,
                'telefone': partner_phone,
                'inscricao_municipal': im_tomador,
                'email': self.partner_id.email or partner.email or '',
            }

            phone = self.company_id.partner_id.phone
            company_ddd = None
            if phone:
                phone = re.sub('[^0-9]', '', phone)
                company_ddd = phone[:2]
                phone = phone[2:]
            city_prestador = self.company_id.partner_id.city_id
            prestador = {
                'cnpj': re.sub(
                    '[^0-9]', '', self.company_id.partner_id.cnpj_cpf or ''),
                'razao_social': self.company_id.partner_id.legal_name or '',
                'inscricao_municipal': re.sub(
                    '[^0-9]', '', self.company_id.partner_id.inscr_mun or ''),
                'cidade': '6291',
                'tipo_logradouro': 'Rua',
                'cnae': self.company_id.cnae_main_id.code,
                'ddd': company_ddd,
                'telefone': phone,
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
            descricao = ''
            valor_servico = 0.0
            valor_deducao = 0.0
            for inv_line in self.eletronic_item_ids:
                descricao += inv_line.product_id.name
                item = {
                    'descricao': inv_line.product_id.name[:80] or '',
                    'quantidade': str("%.0f" % inv_line.quantidade),
                    'valor_unitario': str("%.2f" % (inv_line.preco_unitario)),
                    'valor_total': str(
                        "%.2f" % (
                            inv_line.quantidade * inv_line.preco_unitario)),
                }
                itens.append(item)
                aliquota_pis = inv_line.pis_aliquota
                aliquota_cofins = inv_line.cofins_aliquota
                aliquota_csll = inv_line.csll_aliquota
                aliquota_inss = inv_line.inss_aliquota
                aliquota_ir = inv_line.irrf_aliquota
                aliquota_issqn = inv_line.issqn_aliquota
                valor_servico += inv_line.quantidade * inv_line.preco_unitario

            codigo_atividade = re.sub(
                '[^0-9]', '', self.company_id.cnae_main_id.code)
            tipo_recolhimento = self.operation

            data_envio = datetime.strptime(
                self.data_emissao, DTFT)
            assinatura = '%011dNF   %012d%s%s %s%s%015d%015d%010d%014d' % \
                (int(prestador['inscricao_municipal']),
                 int(numero_rps.zfill(12)),
                 data_envio.strftime('%Y%m%d'), self.taxation,
                 'N', 'N' if tipo_recolhimento == 'A' else 'S',
                 round(valor_servico * 100),
                 round(valor_deducao * 100),
                 int('{:0<9}'.format(codigo_atividade)),
                 int(tomador['cpf_cnpj']))

            assinatura = hashlib.sha1(assinatura.encode()).hexdigest()
            rps = [{
                'assinatura': assinatura,
                'tomador': tomador,
                'prestador': prestador,
                'serie': 'NF',
                'numero': numero_rps,
                'data_emissao': dt_emissao,
                'situacao': 'N',
                'serie_prestacao': self.serie.code,
                'codigo_atividade': '{:0<9}'.format(codigo_atividade),
                'aliquota_atividade': str("%.4f" % aliquota_issqn),
                'tipo_recolhimento': tipo_recolhimento,
                'municipio_prestacao': '6291',
                'municipio_descricao_prestacao': city_prestador.name or '',
                'operacao': self.operation,
                'tributacao': self.taxation,
                'valor_pis': str("%.2f" % self.valor_pis),
                'valor_cofins': str("%.2f" % self.valor_cofins),
                'valor_csll': str("%.2f" % self.valor_retencao_csll),
                'valor_inss': str("%.2f" % self.valor_retencao_inss),
                'valor_ir': str("%.2f" % self.valor_retencao_irrf),
                'aliquota_pis': str("%.2f" % aliquota_pis),
                'aliquota_cofins': str("%.2f" % aliquota_cofins),
                'aliquota_csll': str("%.2f" % aliquota_csll),
                'aliquota_inss': str("%.2f" % aliquota_inss),
                'aliquota_ir': str("%.2f" % aliquota_ir),
                'descricao': descricao,
                'deducoes': deducoes,
                'itens': itens,
            }]

            nfse_vals = {
                'cidade': '6291',
                'cpf_cnpj': prestador['cnpj'],
                'remetente': prestador['razao_social'],
                'transacao': 'true',
                'data_inicio': data_envio.strftime('%Y-%m-%d'),
                'data_fim': data_envio.strftime('%Y-%m-%d'),
                'total_rps': '1',
                'total_servicos': str("%.2f" % self.valor_final),
                'total_deducoes': '0',
                'lote_id': self.id,
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
                name="dsf-%08d.pdf" % int(self.numero_nfse),
                datas_fname="dsf-%08d.pdf" % int(self.numero_nfse),
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

            nfse_values = self._prepare_eletronic_invoice_values()
            cert = self.company_id.with_context(
                {'bin_size': False}).nfe_a1_file
            cert_pfx = base64.decodestring(cert)

            certificado = Certificado(
                cert_pfx, self.company_id.nfe_a1_password)

            if self.ambiente == "producao":
                resposta = enviar(certificado, nfse=nfse_values)
            else:
                resposta = teste_enviar(certificado, nfse=nfse_values)

            retorno = resposta['object']

            if retorno.Cabecalho.Sucesso:
                self.state = 'done'
                self.codigo_retorno = '100'
                self.mensagem_retorno = \
                    'Nota Fiscal de Serviço emitida com sucesso'

                # Apenas producão tem essa tag
                if self.ambiente == 'producao':
                    obj = {
                        'cpf_cnpj': re.sub(
                            '[^0-9]', '', self.company_id.cnpj_cpf),
                        'cidade': '6192',
                        'lote': retorno.Cabecalho.NumeroLote,
                    }

                    consulta_situacao = consulta_lote(consulta=obj)

                    self.verify_code = consulta_situacao.ListaNFSe \
                        .ConsultaNFSe.CodigoVerificacao
                    self.numero_nfse = consulta_situacao.ListaNFSe \
                        .ConsultaNFSe.NumeroNFe
            else:
                self.codigo_retorno = retorno.Erro.Codigo
                self.mensagem_retorno = retorno.Erro.Descricao
                return

            self.env['invoice.eletronic.event'].create({
                'code': self.codigo_retorno,
                'name': self.mensagem_retorno,
                'invoice_eletronic_id': self.id,
            })

            if resposta:
                self._create_attachment(
                    'nfse-ret', self, str(resposta['received_xml']))
                self._create_attachment(
                    'nfse-env', self, str(resposta['sent_xml']))

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
        canc = {
            'nota_id': self.id,
            'cpf_cnpj': re.sub('[^0-9]', '', company.cnpj_cpf),
            'inscricao_municipal': re.sub('[^0-9]', '', company.inscr_mun),
            'cidade': '6192',
            'numero_nfse': self.numero_nfse,
        }
        cancel = cancelar(
            certificado, cancelamento=canc)
        retorno = cancel['object']
        if "NotasCanceladas" in dir(retorno):
            self.state = 'cancel'
            self.codigo_retorno = '100'
            self.mensagem_retorno = u'Nota Fiscal de Serviço Cancelada'
        else:
            mensagem = "%s - %s" % (
                retorno.Erros.erro.Codigo,
                retorno.Erros.erro.Descricao,
            )
            raise UserError(mensagem)

        self.env['invoice.eletronic.event'].create({
            'code': self.codigo_retorno,
            'name': self.mensagem_retorno,
            'invoice_eletronic_id': self.id,
        })
        self._create_attachment('canc', self, cancel['sent_xml'])
        self._create_attachment('canc-ret', self, cancel['received_xml'])
