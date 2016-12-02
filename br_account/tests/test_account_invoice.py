# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests.common import TransactionCase


class TestAccountInvoice(TransactionCase):

    def setUp(self):
        super(TestAccountInvoice, self).setUp()

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
        self.default_product = self.env['product.product'].create({
            'name': 'Normal Product',
            'default_code': '12',
            'list_price': 15.0
        })
        self.service = self.env['product.product'].create({
            'name': 'Normal Service',
            'default_code': '25',
            'type': 'service',
            'fiscal_type': 'service',
            'list_price': 50.0
        })
        self.st_product = self.env['product.product'].create({
            'name': 'Product for ICMS ST',
            'default_code': '15',
            'list_price': 25.0
        })
        self.partner = self.env['res.partner'].create({
            'name': 'Nome Parceiro',
            'is_company': False,
            'property_account_receivable_id': self.receivable_account.id,
        })
        self.journalrec = self.env['account.journal'].create({
            'name': 'Faturas',
            'code': 'INV',
            'type': 'sale',
            'default_debit_account_id': self.revenue_account.id,
            'default_credit_account_id': self.revenue_account.id,
        })
        invoice_line_data = [
            (0, 0,
                {
                    'product_id': self.default_product.id,
                    'quantity': 10.0,
                    'price_unit': self.default_product.list_price,
                    'account_id': self.revenue_account.id,
                    'name': 'product test 5',
                }
             ),
            (0, 0,
                {
                    'product_id': self.service.id,
                    'quantity': 10.0,
                    'price_unit': self.service.list_price,
                    'account_id': self.revenue_account.id,
                    'name': 'product test 5',
                    'product_type': self.service.fiscal_type,
                }
             )
        ]
        default_invoice = {
            'name': u"Teste Validação",
            'reference_type': "none",
            'journal_id': self.journalrec.id,
            'account_id': self.receivable_account.id,
            'invoice_line_ids': invoice_line_data
        }
        self.invoices = self.env['account.invoice'].create(dict(
            default_invoice.items(),
            partner_id=self.partner.id
        ))

    def test_compute_total_values(self):
        for invoice in self.invoices:
            self.assertEquals(invoice.amount_total, 650.0)
            self.assertEquals(invoice.amount_total_signed, 650.0)
            self.assertEquals(invoice.amount_untaxed, 650.0)
            self.assertEquals(invoice.amount_tax, 0.0)
            self.assertEquals(invoice.total_tax, 0.0)

            # Verifico as linhas recebiveis
            self.assertEquals(len(invoice.receivable_move_line_ids), 0)

            # Valido a fatura
            invoice.action_invoice_open()

            # Verifico as linhas recebiveis
            self.assertEquals(len(invoice.receivable_move_line_ids), 1)
