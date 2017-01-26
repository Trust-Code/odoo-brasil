# -*- coding: utf-8 -*-
# © 2016 Alessandro Martini, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import os
import base64
from mock import patch
from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError
from pytrustnfe.xml import sanitize_response


class TestInutilizacao(TransactionCase):

    caminho = os.path.dirname(__file__)

    def setUp(self):
        super(TestInutilizacao, self).setUp()
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
            'nfe_a1_file': base64.b64encode(
                open(os.path.join(self.caminho, 'teste.pfx'), 'r').read()),
        })
        self.revenue_account = self.env['account.account'].create({
            'code': '3.0.0',
            'name': 'Receita de Vendas',
            'user_type_id': self.env.ref(
                'account.data_account_type_revenue').id,
            'company_id': self.main_company.id
        })
        self.receivable_account = self.env['account.account'].create({
            'code': '1.0.0',
            'name': 'Conta de Recebiveis',
            'reconcile': True,
            'user_type_id': self.env.ref(
                'account.data_account_type_receivable').id,
            'company_id': self.main_company.id
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
        default_partner = {
            'name': 'Nome Parceiro',
            'legal_name': 'Razão Social',
            'zip': '88037-240',
            'street': 'Endereço Rua',
            'number': '42',
            'district': 'Centro',
            'phone': '(48) 9801-6226',
            'property_account_receivable_id': self.receivable_account.id,
        }
        self.partner_fisica = self.env['res.partner'].create(dict(
            default_partner.items(),
            cnpj_cpf='545.770.154-98',
            company_type='person',
            is_company=False,
            country_id=self.env.ref('base.br').id,
            state_id=self.env.ref('base.state_br_sc').id,
            city_id=self.env.ref('br_base.city_4205407').id
        ))

        self.journalrec = self.env['account.journal'].create({
            'name': 'Faturas',
            'code': 'INV',
            'type': 'sale',
            'default_debit_account_id': self.revenue_account.id,
            'default_credit_account_id': self.revenue_account.id,
        })

        self.fpos = self.env['account.fiscal.position'].create({
            'name': 'Venda'
        })
        invoice_line_data = [
            (0, 0,
                {
                    'product_id': self.default_product.id,
                    'quantity': 10.0,
                    'account_id': self.revenue_account.id,
                    'name': 'product test 5',
                    'price_unit': 100.00,
                    'cfop_id': self.env.ref(
                        'br_data_account_product.cfop_5101').id,
                    'icms_cst_normal': '40',
                    'icms_csosn_simples': '102',
                    'ipi_cst': '50',
                    'pis_cst': '01',
                    'cofins_cst': '01',
                }
             ),
        ]
        self.default_invoice = {
            'name': "Teste Validação",
            'reference_type': "none",
            'fiscal_document_id': self.env.ref(
                'br_data_account.fiscal_document_55').id,
            'journal_id': self.journalrec.id,
            'account_id': self.receivable_account.id,
            'fiscal_position_id': self.fpos.id,
            'invoice_line_ids': invoice_line_data
        }
        self.fiscal_doc = self.env['br_account.fiscal.document'].create(dict(
            code='1',
        ))
        self.serie = self.env['br_account.document.serie'].create(dict(
            code='1',
            active=True,
            name='serie teste',
            fiscal_document_id=self.fiscal_doc.id,
            fiscal_type='product',
            company_id=self.main_company.id,
        ))

    def tearDown(self):
        inutilized = self.env['invoice.eletronic.inutilized'].search([])
        for number in inutilized:
            self.env['invoice.eletronic.inutilized'].update([
                (2, number.id, 0),
            ])

    @patch('odoo.addons.br_nfe.models.inutilized_nfe.inutilizar_nfe')
    def test_inutilizacao_ok(self, inutilizar):
        with open(os.path.join(self.caminho,
                               'xml/inutilizacao_sent_xml.xml')) as f:
            sent_xml = f.read()
        with open(os.path.join(self.caminho,
                               'xml/inutilizacao_received_xml.xml')) as f:
            received_xml = f.read()
        _, obj = sanitize_response(received_xml)
        inutilizar.return_value = {'received_xml': received_xml,
                                   'sent_xml': sent_xml,
                                   'object': obj}
        justif = 'Sed lorem nibh, sodales ut ex a, tristique ullamcor'
        wizard = self.env['wizard.inutilization.nfe.numeration'].create(dict(
            numeration_start=0,
            numeration_end=5,
            serie=self.serie.id,
            modelo='55',
            justificativa=justif
        ))
        wizard.action_inutilize_nfe()
        inut_inv = self.env['invoice.eletronic.inutilized'].search([])
        self.assertEqual(len(inut_inv), 1)
        self.assertEqual(inut_inv.numeration_start, 0)
        self.assertEqual(inut_inv.numeration_end, 5)
        self.assertEqual(inut_inv.serie, self.serie)
        self.assertEqual(inut_inv.name, u'Série Inutilizada 0 - 5')
        self.assertEqual(inut_inv.justificativa, justif)
        self.assertEqual(inut_inv.state, 'error')
        invoice = self.env['account.invoice'].create(dict(
            self.default_invoice.items(),
            partner_id=self.partner_fisica.id
        ))
        invoice.action_invoice_open()
        inv_eletr = self.env['invoice.eletronic'].search(
            [('invoice_id', '=', invoice.id)])
        self.assertEqual(inv_eletr.numero, 6)

    @patch('odoo.addons.br_nfe.models.inutilized_nfe.inutilizar_nfe')
    def test_inutilizacao_2_sequences(self, inutilizar):
        with open(os.path.join(self.caminho,
                               'xml/inutilizacao_sent_xml.xml')) as f:
            sent_xml = f.read()
        with open(os.path.join(self.caminho,
                               'xml/inutilizacao_received_xml.xml')) as f:
            received_xml = f.read()
        _, obj = sanitize_response(received_xml)
        inutilizar.return_value = {'received_xml': received_xml,
                                   'sent_xml': sent_xml,
                                   'object': obj}
        wizard1 = self.env['wizard.inutilization.nfe.numeration'].create(dict(
            numeration_start=0,
            numeration_end=5,
            serie=self.serie.id,
            modelo='55',
            justificativa='Sed lorem nibh, sodales ut ex a, tristique ullamcor'
        ))
        wizard1.action_inutilize_nfe()
        wizard2 = self.env['wizard.inutilization.nfe.numeration'].create(dict(
            numeration_start=6,
            numeration_end=9,
            serie=self.serie.id,
            modelo='55',
            justificativa='Sed lorem nibh, sodales ut ex a, tristique ullamcor'
        ))
        wizard2.action_inutilize_nfe()
        invoice = self.env['account.invoice'].create(dict(
            self.default_invoice.items(),
            partner_id=self.partner_fisica.id
        ))
        invoice.action_invoice_open()
        inv_eletr = self.env['invoice.eletronic'].search(
            [('invoice_id', '=', invoice.id)])
        self.assertEqual(inv_eletr.numero, 10)

    @patch('odoo.addons.br_nfe.models.inutilized_nfe.inutilizar_nfe')
    def test_inutilizacao_return_ok(self, inutilizar):
        with open(os.path.join(self.caminho,
                               'xml/inutilizacao_sent_xml.xml')) as f:
            sent_xml = f.read()
        with open(os.path.join(self.caminho,
                               'xml/inutilizacao_received_ok_xml.xml')) as f:
            received_xml = f.read()
        _, obj = sanitize_response(received_xml)
        inutilizar.return_value = {'received_xml': received_xml,
                                   'sent_xml': sent_xml,
                                   'object': obj}
        justif = 'Sed lorem nibh, sodales ut ex a, tristique ullamcor'
        wizard = self.env['wizard.inutilization.nfe.numeration'].create(dict(
            numeration_start=0,
            numeration_end=5,
            serie=self.serie.id,
            modelo='55',
            justificativa=justif
        ))
        wizard.action_inutilize_nfe()
        inut_inv = self.env['invoice.eletronic.inutilized'].search([])
        self.assertEqual(len(inut_inv), 1)
        self.assertEqual(inut_inv.numeration_start, 0)
        self.assertEqual(inut_inv.numeration_end, 5)
        self.assertEqual(inut_inv.serie, self.serie)
        self.assertEqual(inut_inv.name, u'Série Inutilizada 0 - 5')
        self.assertEqual(inut_inv.justificativa, justif)
        self.assertEqual(inut_inv.state, 'done')
        invoice = self.env['account.invoice'].create(dict(
            self.default_invoice.items(),
            partner_id=self.partner_fisica.id
        ))
        invoice.action_invoice_open()
        inv_eletr = self.env['invoice.eletronic'].search(
            [('invoice_id', '=', invoice.id)])
        self.assertEqual(inv_eletr.numero, 6)

    def test_inutilizacao_wrong_sqnc(self):
        wizard = self.env['wizard.inutilization.nfe.numeration'].create(dict(
            numeration_start=10,
            numeration_end=5,
            serie=self.serie.id,
            modelo='55',
            justificativa='Sed lorem nibh, sodales ut ex a, tristique ullamcor'
        ))
        invoice = self.env['account.invoice'].create(dict(
            self.default_invoice.items(),
            partner_id=self.partner_fisica.id
        ))
        invoice.action_invoice_open()
        with self.assertRaises(UserError):
            wizard.action_inutilize_nfe()

    def test_inutilizacao_justificativa_short(self):
        wizard = self.env['wizard.inutilization.nfe.numeration'].create(dict(
            numeration_start=10,
            numeration_end=5,
            serie=self.serie.id,
            modelo='55',
            justificativa='Sed lorem'
        ))
        with self.assertRaises(UserError):
            wizard.action_inutilize_nfe()

    def test_inutilizacao_justificativa_long(self):
        wizard = self.env['wizard.inutilization.nfe.numeration'].create(dict(
            numeration_start=10,
            numeration_end=5,
            serie=self.serie.id,
            modelo='55',
            justificativa='Sed lorem' * 255,
        ))
        with self.assertRaises(UserError):
            wizard.action_inutilize_nfe()

    def test_inutilizacao_negative(self):
        wizard = self.env['wizard.inutilization.nfe.numeration'].create(dict(
            numeration_start=-10,
            numeration_end=-1,
            serie=self.serie.id,
            modelo='55',
            justificativa='Sed lorem nibh, sodales ut ex a, tristique ullamcor'
        ))
        with self.assertRaises(UserError):
            wizard.action_inutilize_nfe()

    def test_inutilizacao_sequence_too_long(self):
        wizard = self.env['wizard.inutilization.nfe.numeration'].create(dict(
            numeration_start=1,
            numeration_end=10005,
            serie=self.serie.id,
            modelo='55',
            justificativa='Sed lorem nibh, sodales ut ex a, tristique ullamcor'
        ))
        with self.assertRaises(UserError):
            wizard.action_inutilize_nfe()

    def test_inutilizacao_no_cnpj(self):
        self.main_company.cnpj_cpf = None
        wizard = self.env['wizard.inutilization.nfe.numeration'].create(dict(
            numeration_start=10,
            numeration_end=100,
            serie=self.serie.id,
            modelo='55',
            justificativa='Sed lorem nibh, sodales ut ex a, tristique ullamcor'
        ))
        with self.assertRaises(UserError):
            wizard.action_inutilize_nfe()

    def test_inutilizacao_user_error(self):
        wizard = self.env['wizard.inutilization.nfe.numeration'].create(dict(
            numeration_start=0,
            numeration_end=5,
            serie=self.serie.id,
            modelo='55',
            justificativa='Sed lorem nibh, sodales ut ex a, tristique ullamcor'
        ))
        invoice = self.env['account.invoice'].create(dict(
            self.default_invoice.items(),
            partner_id=self.partner_fisica.id
        ))
        invoice.action_invoice_open()
        with self.assertRaises(UserError):
            wizard.action_inutilize_nfe()
