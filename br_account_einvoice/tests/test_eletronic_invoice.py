# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError


class TestEletronicInvoice(TransactionCase):

    def setUp(self):
        super(TestEletronicInvoice, self).setUp()
        self.main_company = self.env.ref('base.main_company')
        self.currency_real = self.env.ref('base.BRL')

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
        self.service = self.env['product.product'].create({
            'name': 'Normal Service',
            'type': 'service',
            'fiscal_type': 'service',
            'service_type_id': self.env.ref(
                'br_data_account.service_type_101').id,
            'list_price': 50.0
        })
        self.partner_fisica = self.env['res.partner'].create(dict(
            name='Parceiro',
            company_type='company',
            is_company=True,
            property_account_receivable_id=self.receivable_account.id
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
        invoice_line_incomplete = [
            (0, 0,
                {
                    'product_id': self.default_product.id,
                    'quantity': 10.0,
                    'account_id': self.revenue_account.id,
                    'name': 'product test 5',
                    'price_unit': 100.00,
                }
             ),
            (0, 0,
                {
                    'product_id': self.service.id,
                    'quantity': 10.0,
                    'account_id': self.revenue_account.id,
                    'name': 'product test 5',
                    'price_unit': 100.00,
                    'product_type': self.service.fiscal_type,
                }
             )
        ]
        self.inv_incomplete = self.env['account.invoice'].create(dict(
            name="Teste Validação",
            reference_type="none",
            product_document_id=self.env.ref(
                'br_data_account.fiscal_document_55').id,
            journal_id=self.journalrec.id,
            partner_id=self.partner_fisica.id,
            account_id=self.receivable_account.id,
            invoice_line_ids=invoice_line_incomplete
        ))

    def test_basic_validation_for_eletronic_doc(self):
        self.assertEquals(self.inv_incomplete.total_edocs, 0)

        vals = self.inv_incomplete.action_view_edocs()
        self.assertEquals(vals['type'], 'ir.actions.act_window')
        self.assertEquals(vals['res_model'], 'invoice.eletronic')
        self.assertEquals(vals['res_id'], 0)
        with self.assertRaises(UserError):
            self.inv_incomplete.action_invoice_open()

        invoice_eletronic = self.env['invoice.eletronic'].search(
            [('invoice_id', '=', self.inv_incomplete.id)])

        self.assertEquals(self.inv_incomplete.total_edocs, 0)
        vals = self.inv_incomplete.action_view_edocs()
        self.assertEquals(vals['type'], 'ir.actions.act_window')
        self.assertEquals(vals['res_model'], 'invoice.eletronic')
        self.assertEquals(vals['res_id'], invoice_eletronic.id)
