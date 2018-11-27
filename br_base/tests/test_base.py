# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import os
import base64
import logging
from mock import patch
from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)

try:
    from pytrustnfe.xml import sanitize_response
except ImportError:
    _logger.error('Cannot import pytrustnfe', exc_info=True)


class TestBase(TransactionCase):

    caminho = os.path.dirname(__file__)

    def test_parceiro_cpf_valido(self):
        partner = self.env['res.partner'].create({
            'name': 'Parceiro Ok',
            'cnpj_cpf': '99644045491',
            'country_id': self.env.ref('base.br').id
        })
        self.assertTrue(partner)

    def test_parceiro_com_rg(self):
        partner = self.env['res.partner'].create({
            'name': 'Parceiro Ok',
            'cnpj_cpf': '99644045491',
            'inscr_est': '123',
            'country_id': self.env.ref('base.br').id
        })
        self.assertTrue(partner)

    def test_cpf_invalido(self):
        with self.assertRaises(ValidationError):
            self.env['res.partner'].create({
                'name': 'Parceiro Ok',
                'cnpj_cpf': '99644045490',
                'country_id': self.env.ref('base.br').id
            })

    def test_cnpj_valido(self):
        partner = self.env['res.partner'].create({
            'name': 'Empresa',
            'cnpj_cpf': '22814429000155',
            'is_company': True,
            'country_id': self.env.ref('base.br').id
        })
        self.assertTrue(partner)

    def test_cnpj_invalido(self):
        with self.assertRaises(ValidationError):
            self.env['res.partner'].create({
                'name': 'Empresa',
                'cnpj_cpf': '99644045490',
                'is_company': True,
                'country_id': self.env.ref('base.br').id
            })

    def test_ie_valido(self):
        partner = self.env['res.partner'].create({
            'name': 'Empresa',
            'cnpj_cpf': '22814429000155',
            'inscr_est': '112.632.165',
            'is_company': True,
            'country_id': self.env.ref('base.br').id,
            'state_id': self.env.ref('base.state_br_sc').id,
        })
        self.assertTrue(partner)

    def test_ie_invalido(self):
        with self.assertRaises(ValidationError):
            self.env['res.partner'].create({
                'name': 'Empresa',
                'cnpj_cpf': '22814429000155',
                'inscr_est': '112165',
                'is_company': True,
                'country_id': self.env.ref('base.br').id,
                'state_id': self.env.ref('base.state_br_sc').id,
            })

    def test_ie_duplicated(self):
        vals = {
            'name': 'Empresa',
            'cnpj_cpf': '22814429000155',
            'inscr_est': '112.632.165',
            'is_company': True,
            'country_id': self.env.ref('base.br').id,
            'state_id': self.env.ref('base.state_br_sc').id,
        }
        partner = self.env['res.partner'].create(vals)
        self.assertTrue(partner)
        with self.assertRaises(ValidationError):
            vals['cnpj_cpf'] = '63.116.726/0001-04'
            self.env['res.partner'].create(vals)
        vals['inscr_est'] = False
        vals['cnpj_cpf'] = '07.343.961/0001-48'
        partner = self.env['res.partner'].create(vals)
        self.assertTrue(partner)

    def test_onchange_cnpj(self):
        partner = self.env['res.partner'].create({
            'name': 'Empresa',
            'cnpj_cpf': '22814429000155',
            'is_company': True,
            'country_id': self.env.ref('base.br').id,
        })
        self.assertEquals(partner.cnpj_cpf, '22814429000155')
        partner._onchange_cnpj_cpf()
        self.assertEquals(partner.cnpj_cpf, '22.814.429/0001-55')

    def test_onchange_cpf(self):
        partner = self.env['res.partner'].create({
            'name': 'Empresa',
            'cnpj_cpf': '71194004016',
            'country_id': self.env.ref('base.br').id,
        })
        self.assertEquals(partner.cnpj_cpf, '71194004016')
        partner._onchange_cnpj_cpf()
        self.assertEquals(partner.cnpj_cpf, '711.940.040-16')

    def test_onchange_zip(self):
        partner = self.env['res.partner'].create({
            'name': 'Parceiro',
            'zip': '88032050',
        })
        self.assertEquals(partner.zip, '88032050')
        partner.onchange_mask_zip()
        self.assertEquals(partner.zip, '88032-050')

    def test_onchange_city(self):
        city = self.env.ref('br_base.city_3205002')
        partner = self.env['res.partner'].create({
            'name': 'Parceiro',
            'city_id': city.id,
        })
        self.assertEquals(partner.city_id, city)
        partner._onchange_city_id()
        self.assertEquals(partner.city, city.name)

    def test_display_address(self):
        partner = self.env['res.partner'].create({
            'name': 'Empresa',
            'cnpj_cpf': '22814429000155',
            'inscr_est': '112.632.165',
            'is_company': True,
            'state_id': self.env.ref('base.state_br_sc').id,
            'city_id': self.env.ref('br_base.city_3205002').id,
            'country_id':  self.env.ref('base.us').id
        })
        partner._display_address()
        partner.country_id = self.env.ref('base.br').id
        partner._display_address()

    @patch('odoo.addons.br_base.models.res_partner.consulta_cadastro')
    def test_consulta_cadastro(self, consulta):
        partner = self.env['res.partner'].create({
            'name': 'Empresa',
            'cnpj_cpf': '22814429000155',
            'is_company': True,
            'country_id': self.env.ref('base.br').id,
            'state_id': self.env.ref('base.state_br_sc').id,
        })
        with self.assertRaises(UserError):
            partner.action_check_sefaz()
        self.env.ref('base.main_company').nfe_a1_password = '123456'
        self.env.ref('base.main_company').nfe_a1_file = base64.b64encode(
            open(os.path.join(self.caminho, 'teste.pfx'), 'rb').read())

        # Consulta cadastro com sucesso
        xml_recebido = open(os.path.join(
            self.caminho, 'xml/consulta_cadastro.xml'), 'r').read()
        resp = sanitize_response(xml_recebido)
        consulta.return_value = {
            'object': resp[1],
            'sent_xml': '<xml />',
            'received_xml': xml_recebido
        }

        partner.action_check_sefaz()
        self.assertEquals(partner.cnpj_cpf, '22814429000155')
        self.assertEquals(partner.inscr_est, '112632165')
        self.assertEquals(partner.street, 'RUA PADRE JOAO')
        self.assertEquals(partner.district, 'Centro')
        self.assertEquals(partner.city_id.id, 3776)
        self.assertEquals(partner.zip, '88032050')

    def test_company_compute_fields(self):
        company = self.env.ref('base.main_company')

        company.cnpj_cpf = '62.565.938/0001-06'
        company.suframa = '456'
        company.legal_name = 'Razão Social'
        company.inscr_est = 'ISENTO'
        company.inscr_mun = '987654'
        company.number = 12
        company.district = 'Centro'
        company.city_id = self.env.ref('br_base.city_3205002').id
        self.assertEquals(company.partner_id.cnpj_cpf, company.cnpj_cpf)
        self.assertEquals(company.partner_id.suframa, company.suframa)
        self.assertEquals(company.partner_id.legal_name, company.legal_name)
        self.assertEquals(company.partner_id.inscr_est, company.inscr_est)
        self.assertEquals(company.partner_id.inscr_mun, company.inscr_mun)
        self.assertEquals(company.partner_id.number, company.number)
        self.assertEquals(company.partner_id.city_id, company.city_id)

    def test_company_inverse_fields(self):
        company = self.env.ref('base.main_company')

        company.partner_id.cnpj_cpf = '62.565.938/0001-06'
        company.partner_id.suframa = '456'
        company.partner_id.legal_name = 'Razão Social'
        company.partner_id.inscr_est = 'ISENTO'
        company.partner_id.inscr_mun = '987654'
        company.partner_id.number = 12
        company.partner_id.district = 'Centro'
        company.partner_id.city_id = self.env.ref('br_base.city_3205002').id
        self.assertEquals(company.partner_id.cnpj_cpf, company.cnpj_cpf)
        self.assertEquals(company.partner_id.suframa, company.suframa)
        self.assertEquals(company.partner_id.legal_name, company.legal_name)
        self.assertEquals(company.partner_id.inscr_est, company.inscr_est)
        self.assertEquals(company.partner_id.inscr_mun, company.inscr_mun)
        self.assertEquals(company.partner_id.number, company.number)
        self.assertEquals(company.partner_id.city_id, company.city_id)

    def test_onchanges_company(self):
        company = self.env.ref('base.main_company')
        company.cnpj_cpf = '62565938000106'
        company.onchange_mask_cnpj_cpf()
        self.assertEquals(company.cnpj_cpf, '62.565.938/0001-06')
        company.zip = '88032050'
        company.onchange_mask_zip()
        self.assertEquals(company.zip, '88032-050')

    def test_company_onchange_city(self):
        company = self.env.ref('base.main_company')
        city = self.env.ref('br_base.city_3205002')
        company.update({
            'city_id': city.id,
        })
        self.assertEquals(company.city_id, city)
        company.onchange_city_id()
        self.assertEquals(company.city, city.name)
