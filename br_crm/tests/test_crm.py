# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError


class TestCrm(TransactionCase):

    def test_cpf_valido(self):
        lead = self.env['crm.lead'].create({
            'name': 'Lead',
            'cpf': '42590472137'
        })
        self.assertTrue(lead)
        lead.onchange_mask_cpf()
        self.assertEquals(lead.cpf, '425.904.721-37')

    def test_cpf_invalido(self):
        with self.assertRaises(ValidationError):
            self.env['crm.lead'].create({
                'name': 'Lead',
                'cpf': '4259047213'
            })

    def test_cnpj_valido(self):
        lead = self.env['crm.lead'].create({
            'name': 'Lead',
            'cnpj': '94175147000166'
        })
        self.assertTrue(lead)
        lead.onchange_mask_cnpj()
        self.assertEquals(lead.cnpj, '94.175.147/0001-66')

    def test_cnpj_invalido(self):
        with self.assertRaises(ValidationError):
            self.env['crm.lead'].create({
                'name': 'Lead',
                'cnpj': '9417514700016'
            })

    def test_inscricao_estadual_valida(self):
        lead = self.env['crm.lead'].create({
            'name': 'Empresa',
            'inscr_est': '112.632.165',
            'country_id': self.env.ref('base.br').id,
            'state_id': self.env.ref('base.state_br_sc').id,
        })
        self.assertTrue(lead)
        lead.inscr_est = 'ISENTO'

    def test_ie_invalido(self):
        with self.assertRaises(ValidationError):
            self.env['crm.lead'].create({
                'name': 'Empresa',
                'inscr_est': '112165',
                'country_id': self.env.ref('base.br').id,
                'state_id': self.env.ref('base.state_br_sc').id,
            })

    def test_onchanges(self):
        lead = self.env['crm.lead'].create({
            'name': 'Empresa',
        })
        partner = self.env['res.partner'].create({
            'name': 'Empresa',
            'cnpj_cpf': '22814429000155',
            'inscr_est': '112.632.165',
            'is_company': True,
            'legal_name': 'Razão social',
            'suframa': '123456',
            'district': 'Centro',
            'city_id': self.env.ref('br_base.city_3205002').id,
        })
        lead.partner_id = partner.id
        lead._onchange_partner_id()
        lead.onchange_city_id()
        self.assertEquals(lead.legal_name, partner.legal_name)
        self.assertEquals(lead.cnpj, partner.cnpj_cpf)
        self.assertEquals(lead.inscr_est, partner.inscr_est)
        self.assertEquals(lead.suframa, partner.suframa)
        self.assertEquals(lead.district, partner.district)
        self.assertEquals(lead.city_id, partner.city_id)
        self.assertEquals(lead.city, partner.city_id.name)

    def test_convert_lead_company(self):
        wiz = self.env['crm.lead2opportunity.partner'].create({
            'name': 'convert'
        })
        lead = self.env['crm.lead'].create({
            'name': 'New Lead',
            'partner_name': 'Empresa',
            'cnpj': '22814429000155',
            'inscr_est': '112.632.165',
            'inscr_mun': '123456',
            'legal_name': 'Razão social',
            'suframa': '123456',
            'district': 'Centro',
            'city_id': self.env.ref('br_base.city_3205002').id,
        })
        values = {'lead_ids': [lead.id]}
        wiz._convert_opportunity(values)
        self.assertTrue(lead.partner_id)
        self.assertEquals(lead.partner_id.legal_name, lead.legal_name)
        self.assertEquals(lead.partner_id.cnpj_cpf, lead.cnpj)
        self.assertEquals(lead.partner_id.inscr_est, lead.inscr_est)
        self.assertEquals(lead.partner_id.suframa, lead.suframa)
        self.assertEquals(lead.partner_id.inscr_mun, lead.inscr_mun)

    def test_convert_lead_contact(self):
        wiz = self.env['crm.lead2opportunity.partner'].create({
            'name': 'convert'
        })
        lead = self.env['crm.lead'].create({
            'name': 'New Lead',
            'contact_name': 'Empresa',
            'name_surname': 'Empresa',
            'cpf': '709.381.660-69',
            'rg': '987654',
            'city_id': self.env.ref('br_base.city_3205002').id,
        })
        values = {'lead_ids': [lead.id]}
        wiz._convert_opportunity(values)
        self.assertTrue(lead.partner_id)
        self.assertEquals(lead.partner_id.legal_name, lead.name_surname)
        self.assertEquals(lead.partner_id.cnpj_cpf, lead.cpf)
        self.assertEquals(lead.partner_id.inscr_est, lead.rg)
