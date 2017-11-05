# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests.common import TransactionCase


class TestBoleto(TransactionCase):

    def _return_payment_mode(self):
        pass

    def setUp(self):
        super(TestBoleto, self).setUp()
        self.main_company = self.env.ref('base.main_company')
        self.currency_real = self.env.ref('base.BRL')
        self.main_company.write(dict(
            zip='', street='', state_id=False
        ))

        self.revenue_account = self.env['account.account'].create({
            'code': '3.0.0',
            'name': 'Receita de Vendas',
            'user_type_id': self.env.ref(
                'account.data_account_type_revenue').id,
            'company_id': self.main_company.id
        })
        self.receivable_account = self.env['account.account'].create({
            'code': '1.0.0',
            'name': u'Conta de Recebíveis',
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
        self.partner_fisica = self.env['res.partner'].create(dict(
            name='Parceiro',
            company_type='person',
            is_company=False,
            street='Donicia',
            number=45,
            property_account_receivable_id=self.receivable_account.id
        ))
        self.journalrec = self.env['account.journal'].create({
            'name': 'Faturas',
            'code': 'NF',
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
        default_invoice = {
            'name': "Teste Validação",
            'reference_type': "none",
            'fiscal_document_id': self.env.ref(
                'br_data_account.fiscal_document_01').id,
            'journal_id': self.journalrec.id,
            'account_id': self.receivable_account.id,
            'fiscal_position_id': self.fpos.id,
            'invoice_line_ids': invoice_line_data,
            'payment_mode_id': self._return_payment_mode(),
        }
        self.invoices = self.env['account.invoice'].create(dict(
            default_invoice.items(),
            partner_id=self.partner_fisica.id
        ))
