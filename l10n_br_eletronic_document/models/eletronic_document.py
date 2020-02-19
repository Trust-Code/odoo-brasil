import re
import json
import requests
from odoo import api, fields, models
from odoo.exceptions import UserError

from .cst import CST_PIS_COFINS


STATE = {'edit': [('readonly', False)]}


class EletronicDocument(models.Model):
    _name = 'eletronic.document'
    _description = 'Eletronic documents (NFE, NFSe)'
    
    name = fields.Char(string='Name', size=30)
    company_id = fields.Many2one('res.company')
    currency_id = fields.Many2one(
        'res.currency', related='company_id.currency_id',
        string="Company Currency")
    emission_date = fields.Datetime(string="Data de Emissão")
    identifier = fields.Char(string="Identificador")
    
    partner_id = fields.Many2one('res.partner')
    partner_cpf_cnpj = fields.Char(string="CNPJ/CPF", size=20)
    
    document_line_ids = fields.One2many(
        'eletronic.document.line', 'eletronic_document_id', string="Linhas")

    # ------------ PIS ---------------------
    pis_cst = fields.Selection(
        CST_PIS_COFINS, string='Situação Tributária',
        readonly=True, states=STATE)
    pis_aliquota = fields.Float(
        string=u'Alíquota', digits='Account',
        readonly=True, states=STATE)
    pis_base_calculo = fields.Monetary(
        string='Base de Cálculo', digits='Account',
        readonly=True, states=STATE)
    pis_valor = fields.Monetary(
        string='Valor Total', digits='Account',
        readonly=True, states=STATE)
    pis_valor_retencao = fields.Monetary(
        string='Valor Retido', digits='Account',
        readonly=True, states=STATE)

    # ------------ COFINS ------------
    cofins_cst = fields.Selection(
        CST_PIS_COFINS, string='Situação Tributária',
        readonly=True, states=STATE)
    cofins_aliquota = fields.Float(
        string='Alíquota', digits='Account',
        readonly=True, states=STATE)
    cofins_base_calculo = fields.Monetary(
        string='Base de Cálculo', digits='Account',
        readonly=True, states=STATE)
    cofins_valor = fields.Monetary(
        string='Valor Total', digits='Account',
        readonly=True, states=STATE)
    cofins_valor_retencao = fields.Monetary(
        string='Valor Retido', digits='Account',
        readonly=True, states=STATE)

    # ----------- ISS -------------
    iss_codigo = fields.Char(
        string='Código', size=10, readonly=True, states=STATE)
    iss_aliquota = fields.Float(
        string='Alíquota', digits='Account',
        readonly=True, states=STATE)
    iss_base_calculo = fields.Monetary(
        string='Base de Cálculo', digits='Account',
        readonly=True, states=STATE)
    iss_valor = fields.Monetary(
        string='Valor Total', digits='Account',
        readonly=True, states=STATE)
    iss_valor_retencao = fields.Monetary(
        string='Valor Retenção', digits='Account',
        readonly=True, states=STATE)

    # ------------ RETENÇÔES ------------
    csll_base_calculo = fields.Monetary(
        string='Base de Cálculo', digits='Account',
        readonly=True, states=STATE)
    csll_aliquota = fields.Float(
        string='Alíquota', digits='Account',
        readonly=True, states=STATE)
    csll_valor_retencao = fields.Monetary(
        string='Valor Retenção', digits='Account',
        readonly=True, states=STATE)
    irrf_base_calculo = fields.Monetary(
        string='Base de Cálculo', digits='Account',
        readonly=True, states=STATE)
    irrf_aliquota = fields.Float(
        string='Alíquota', digits='Account',
        readonly=True, states=STATE)
    irrf_valor_retencao = fields.Monetary(
        string='Valor Retenção', digits='Account',
        readonly=True, states=STATE)
    inss_base_calculo = fields.Monetary(
        string='Base de Cálculo', digits='Account',
        readonly=True, states=STATE)
    inss_aliquota = fields.Float(
        string='Alíquota', digits='Account',
        readonly=True, states=STATE)
    inss_valor_retencao = fields.Monetary(
        string='Valor Retenção', digits='Account',
        readonly=True, states=STATE)

    valor_final = fields.Monetary(
        string='Valor Final', readonly=True, states=STATE)
    

    def generate_dict_values(self):
        dict_docs = []
        for doc in self:
            partner = doc.partner_id

            emissor = {
                'cnpj': re.sub('[^0-9]', '', doc.company_id.l10n_br_cnpj_cpf or ''),
                'inscricao_municipal': re.sub('[^0-9]', '', doc.company_id.l10n_br_inscr_mun or ''),
                'codigo_municipio': '%s%s' % (
                    doc.company_id.state_id.l10n_br_ibge_code,
                    doc.company_id.city_id.l10n_br_ibge_code),
            }
            tomador = {
                'cpf': re.sub(
                    '[^0-9]', '', partner.l10n_br_cnpj_cpf or ''),
                'inscricao_municipal': re.sub(
                    '[^0-9]', '', partner.l10n_br_inscr_mun or
                    '0000000'),
                'razao_social': partner.l10n_br_legal_name or partner.name,
                'telefone': re.sub('[^0-9]', '', self.partner_id.phone or ''),
                'email': self.partner_id.email,
                'endereco': {
                    'logradouro': partner.street,
                    'numero': partner.l10n_br_number,
                    'bairro': partner.l10n_br_district,
                    'complemento': partner.street2,
                    'cep': re.sub('[^0-9]', '', partner.zip or ''),
                    'codigo_municipio': '%s%s' % (
                        partner.state_id.l10n_br_ibge_code,
                        partner.city_id.l10n_br_ibge_code),
                    'uf': partner.state_id.code,
                }
            }
            items = []
            for line in doc.document_line_ids:
                aliquota = line.issqn_aliquota / 100
                base = line.issqn_base_calculo
                unitario = round(line.valor_liquido / line.quantidade, 2)
                items.append({
                    'name': line.product_id.name,
                    'cnae': re.sub(
                        '[^0-9]', '',
                        line.product_id.service_type_id.id_cnae or ''),
                    'cst_servico': '1',
                    'aliquota': aliquota,
                    'base_calculo': base,
                    'valor_unitario': unitario,
                    'quantidade': int(line.quantidade),
                    'valor_total': line.valor_liquido,
                })
            emissao = fields.Datetime.from_string(doc.emission_date)
            outra_cidade = doc.company_id.city_id.id != partner.city_id.id
            outro_estado = doc.company_id.state_id.id != partner.state_id.id
            outro_pais = doc.company_id.country_id.id != partner.country_id.id

            data = {
                'ambiente': 'homologacao',
                'emissor': emissor,
                'tomador': tomador,
                'numero': "%06d" % doc.identifier,
                'outra_cidade': outra_cidade,
                'outro_estado': outro_estado,
                'outro_pais': outro_pais,
                'regime_tributario': doc.company_id.l10n_br_tax_regime,
                'itens_servico': items,
                'data_emissao': emissao.strftime('%Y-%m-%d'),
                'base_calculo': doc.iss_base_calculo,
                'valor_iss': doc.iss_valor,
                'valor_total': doc.valor_final,
                
                'aedf': doc.company_id.l10n_br_aedf,
                'client_id': doc.company_id.l10n_br_client_id,
                'client_secret': doc.company_id.l10n_br_client_secret,
                'user_password': doc.company_id.l10n_br_user_password,
                'observacoes': '',
            }
            dict_docs.append(data)
        return dict_docs
   
    
    def generate(self):
        company = self.mapped('company_id').with_context({'bin_size': False})
        
        certificate = company.l10n_br_certificate
        password = company.l10n_br_cert_password
        doc_values = self.generate_dict_values()

        response = {}
        if doc_values[0]['emissor']['codigo_municipio'] == '4205407':
            from .nfse_florianopolis import send_api
            response = send_api(certificate, password, doc_values)
        elif doc_values[0]['emissor']['codigo_municipio'] == '3550308':
            from .nfse_paulistana import send_api
            response = send_api(certificate, password, doc_values)
        else:
            from .focus_nfse import send_api
            response = send_api(certificate, password, doc_values)
        
        if response['code'] in (200, 201):
            print(response)
        else:
            raise UserError('%s - %s' % (response['api_code'], response['message']))


class EletronicDocumentLine(models.Model):
    _name = 'eletronic.document.line'
    _description = 'Eletronic document line (NFE, NFSe)'
      
    name = fields.Char(string='Name', size=30)
    company_id = fields.Many2one(
        'res.company', 'Empresa')
    eletronic_document_id = fields.Many2one(
        'eletronic.document', string='Documento')
    currency_id = fields.Many2one(
        'res.currency', related='company_id.currency_id',
        string="Company Currency")
    