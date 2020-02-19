import re
import json
import requests
from odoo import api, fields, models
from odoo.exceptions import UserError


class EletronicDocument(models.Model):
    _name = 'eletronic.document'
    _description = 'Eletronic documents (NFE, NFSe)'
    
    name = fields.Char(string='Name', size=30)
    
    company_id = fields.Many2one('res.company')
    partner_id = fields.Many2one('res.partner')
    partner_cpf_cnpj = fields.Char(string="CNPJ/CPF", size=20)
    document_line_ids = fields.One2many(
        'eletronic.document.line', 'eletronic_document_id', string="Linhas")


    def generate_dict_values(self):
        dict_docs = []
        for doc in self:
            partner = doc.partner_id

            emissor = {
                'cnpj': re.sub('[^0-9]', '', doc.company_id.l10n_br_cnpj_cpf or ''),
                'inscricao_municipal': re.sub('[^0-9]', '', doc.company_id.inscr_mun or ''),
                'codigo_municipio': '%s%s' % (
                    doc.company_id.state_id.ibge_code,
                    doc.company_id.city_id.ibge_code),
            }
            tomador = {
                'cpf': re.sub(
                    '[^0-9]', '', partner.cnpj_cpf or ''),
                'inscricao_municipal': re.sub(
                    '[^0-9]', '', partner.inscr_mun or
                    '0000000'),
                'razao_social': partner.legal_name or partner.name,
                'telefone': re.sub('[^0-9]', '', self.partner_id.phone or ''),
                'email': self.partner_id.email,
                'endereco': {
                    'logradouro': partner.street,
                    'numero': partner.number,
                    'bairro': partner.district,
                    'complemento': partner.street2,
                    'cep': re.sub('[^0-9]', '', partner.zip or ''),
                    'codigo_municipio': '%s%s' % (
                        partner.state_id.ibge_code,
                        partner.city_id.ibge_code),
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
            emissao = fields.Datetime.from_string(doc.data_emissao)
            outra_cidade = doc.company_id.city_id.id != partner.city_id.id
            outro_estado = doc.company_id.state_id.id != partner.state_id.id
            outro_pais = doc.company_id.country_id.id != partner.country_id.id

            data = {
                'emissor': emissor,
                'tomador': tomador,
                'numero': "%06d" % doc.numero,
                'itens_servico': items,
                'data_emissao': emissao.strftime('%Y-%m-%d'),
                'base_calculo': doc.valor_bc_issqn,
                'valor_iss': doc.valor_issqn,
                'valor_total': doc.valor_final,
                'aedf': doc.company_id.aedf,
                'observacoes': '',
            }
            dict_docs.append(data)
        return dict_docs
   
    
    def generate(self):
        company = self.mapped('company_id').with_context({'bin_size': False})
        
        certificate = company.l10n_br_certificate
        password = company.l10n_br_cert_password
        doc_values = self.generate_dict_values()
        
        if nfse_values['emissor']['codigo_municipio'] == '4205407':
            from .nfse_florianopolis import send_api
            send_api(certificate, password, doc_values)
        elif nfse_values['emissor']['codigo_municipio'] == '3550308':
            from .nfse_paulistana import send_api
            send_api(certificate, password, doc_values)
        else:
            from .focus_nfse import send_api
            send_api(certificate, password, doc_values)


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
    