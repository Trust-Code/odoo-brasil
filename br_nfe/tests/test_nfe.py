# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import os
import base64
from odoo.tests.common import TransactionCase


class TestNFeBrasil(TransactionCase):

    caminho = os.path.dirname(__file__)

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
            'country_id': self.env.ref('base.br').id,
            'state_id': self.env.ref('base.state_br_sc').id,
            'city_id': self.env.ref('br_base.city_4205407').id,
            'phone': '(48) 9801-6226',
            'currency_id': self.currency_real.id,
            'nfe_a1_password': '123456',
            'nfe_a1_file': base64.b64encode(open(os.path.join(self.caminho, 'teste.pfx'), 'r').read()),
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
            'cnpj_cpf': '545.770.154-98',
            'company_type': 'person',
            'is_company': False,
            'name': 'Danimar',
            'zip': '88037-240',
            'street': 'Donicia Maria da Costa',
            'number': '42',
            'district': 'Saco Grande',
            'country_id': self.env.ref('base.br').id,
            'state_id': self.env.ref('base.state_br_sc').id,
            'city_id': self.env.ref('br_base.city_4205407').id,
            'phone': '(48) 9801-6226',
        })
        self.partner_juridica = self.env['res.partner'].create({
            'cnpj_cpf': '05.075.837/0001-13',
            'company_type': 'company',
            'is_company': True,
            'name': 'Ficticia',
            'legal_name': 'Empresa Ficticia',
            'inscr_est': '433.992.727',
            'zip': '88032-240',
            'street': 'Endereço Rua',
            'number': '42',
            'district': 'Centro',
            'country_id': self.env.ref('base.br').id,
            'state_id': self.env.ref('base.state_br_sc').id,
            'city_id': self.env.ref('br_base.city_4205407').id,
            'phone': '(48) 9999-9999',
        })

        account_type = self.env.ref('account.data_account_type_receivable')
        self.journalrec = self.env['account.journal'].search(
            [('type', '=', 'sale')])[0]
        self.account_rec1_id = self.env['account.account'].sudo().create(dict(
            code="cust_acc",
            name="customer account",
            user_type_id=account_type.id,
            reconcile=True,
        ))
        self.fpos = self.env['account.fiscal.position'].create({
            'name': 'Venda'
        })
        self.cfop = self.env

    def test_validate_invoice(self):
        invoice_line_data = [
            (0, 0,
                {
                    'product_id': self.default_product.id,
                    'quantity': 10.0,
                    'account_id': self.env['account.account'].search([('user_type_id', '=', self.env.ref('account.data_account_type_revenue').id)], limit=1).id,
                    'name': 'product test 5',
                    'price_unit': 100.00,
                    'cfop_id': self.env.ref('br_data_account_product.cfop_5101').id,
                    'icms_cst_normal': '40',
                    'icms_csosn_simples': '102',
                    'ipi_cst': '50',
                    'pis_cst': '01',
                    'cofins_cst': '01',
                }
             )
        ]

        self.inv = self.env['account.invoice'].create(dict(
            name="Test Customer Invoice",
            reference_type="none",
            fiscal_document_id=self.env.ref('br_data_account.fiscal_document_55').id,
            fiscal_position_id=self.fpos.id,
            journal_id=self.journalrec.id,
            partner_id=self.partner_fisica.id,
            account_id=self.account_rec1_id.id,
            invoice_line_ids=invoice_line_data
        ))
        self.inv.action_invoice_open()
        vals = self.inv.action_view_edocs()

        self.assertEquals(self.inv.total_edocs, 1)
        self.assertEquals(vals['view_id'][1], u'sped.eletronic.doc.form')

        invoice_eletronic = self.env['invoice.eletronic'].search(
            [('invoice_id', '=', self.inv.id)])
        with self.assertRaises(Exception):
            invoice_eletronic.action_send_eletronic_invoice()
