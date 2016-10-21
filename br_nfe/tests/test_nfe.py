# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests.common import TransactionCase


class TestNFeBrasil(TransactionCase):

    def setUp(self):
        super(TestNFeBrasil, self).setUp()
        self.main_company = self.env.ref('base.main_company')
        self.currency_real = self.env.ref('base.BRL')
        self.main_company.write({
            'name': 'Trustcode',
            'legal_name': 'Trustcode Tecnologia da Informação',
            'cnpj_cpf': '92.743.275/0001-33',
            'inscr_est': '219.882.606',
            'zip': '88037-240',
            'street': 'Vinicius de Moraes',
            'number': '42',
            'district': 'Córrego Grande',
            'country_id': self.env.ref('base.br'),
            'state_id': self.env.ref('base.state_br_sc'),
            'city_id': self.env.ref('br_base.city_4205407'),
            'phone': '(48) 9801-6226',
            'currency_id': self.currency_real,
        })

        self.default_ncm = self.env['product.fiscal.classification'].create({
            'code': '0201.20.20',
            'name': 'Furniture',
            'federal_nacional': 10.0,
            'estadual_imposto': 10.0,
            'municipal_imposto': 10.0,
            'cest': '123'
        })
        self.default_product = self.env['product.product'].create({
            'name': 'Normal Product',
            'default_code': '12',
            'fiscal_classification_id': self.default_ncm.id,
            'list_price': 15.0
        })
        self.st_product = self.env['product.product'].create({
            'name': 'Product for ICMS ST',
            'default_code': '15',
            'fiscal_classification_id': self.default_ncm.id,
            'list_price': 25.0
        })
        self.partner_fisica = self.env['res.partner'].create({
            'cnpj_cpf': '788.295.487-07',
            'name': 'Danimar',
            'zip': '88037-240',
            'street': 'Donicia Maria da Costa',
            'number': '42',
            'district': 'Saco Grande',
            'country_id': self.env.ref('base.br'),
            'state_id': self.env.ref('base.state_br_sc'),
            'city_id': self.env.ref('br_base.city_4205407'),
            'phone': '(48) 9801-6226',
        })
        self.partner_juridica = self.env['res.partner'].create({
            'cnpj_cpf': '05.075.837/0001-13',
            'legal_name': 'Empresa Ficticia',
            'inscr_est': '433.992.727',
            'zip': '88032-240',
            'street': 'Endereço Rua',
            'number': '42',
            'district': 'Centro',
            'country_id': self.env.ref('base.br'),
            'state_id': self.env.ref('base.state_br_sc'),
            'city_id': self.env.ref('br_base.city_4205407'),
            'phone': '(48) 9999-9999',
        })

    def test_sale_order_taxes(self):
        print "oi"
